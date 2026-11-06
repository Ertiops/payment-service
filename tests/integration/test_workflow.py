import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select, update
from uuid6 import uuid7

from app.adapters.database.config import DatabaseConfig
from app.adapters.database.storages.outbox import OutboxStorage
from app.adapters.database.storages.payment import PaymentStorage
from app.adapters.database.tables import OutboxTable, PaymentTable
from app.adapters.database.uow import SqlalchemyUow
from app.application.exceptions import EntityAlreadyExistsException
from app.domain.entities.payment import (
    ClaimPaymentAttempt,
    CreatePayment,
    PaymentAttempt,
    PaymentStatus,
    ProcessPayment,
    RecoverPaymentAttempt,
    SaveGatewayResult,
)
from app.domain.processing import ProcessingConfig
from app.domain.use_cases.payment.create import CreatePaymentUC
from app.domain.use_cases.payment.process import ProcessPaymentUC
from app.domain.use_cases.payment.recover import RecoverPaymentAttemptUC
from tests.plugins.use_cases.payment import FakePaymentGateway, FakePaymentWebhookSender
from tests.utils.durable_database import DurableDatabase, durable_database


@pytest.fixture
async def durable_db(db_config: DatabaseConfig) -> AsyncIterator[DurableDatabase]:
    async with durable_database(db_config.dsn) as database:
        yield database


def creation(key: str) -> CreatePayment:
    return CreatePayment(
        amount=Decimal("10.50"),
        currency="USD",
        description="integration",
        meta_data={"order": "1"},
        status=PaymentStatus.PENDING,
        idempotency_key=key,
        webhook_url="https://example.invalid/webhook",
    )


def create_case(database: DurableDatabase) -> CreatePaymentUC:
    session = database.sessions()
    return CreatePaymentUC(
        uow=SqlalchemyUow(session),
        payment_storage=PaymentStorage(session),
        outbox_storage=OutboxStorage(session),
    )


def process_case(
    database: DurableDatabase,
    gateway: FakePaymentGateway,
    sender: FakePaymentWebhookSender,
) -> ProcessPaymentUC:
    session = database.sessions()
    return ProcessPaymentUC(
        uow=SqlalchemyUow(session),
        payment_storage=PaymentStorage(session),
        outbox_storage=OutboxStorage(session),
        payment_gateway=gateway,
        payment_webhook_sender=sender,
        config=ProcessingConfig(),
    )


def recover_case(database: DurableDatabase) -> RecoverPaymentAttemptUC:
    session = database.sessions()
    return RecoverPaymentAttemptUC(
        uow=SqlalchemyUow(session),
        payment_storage=PaymentStorage(session),
        outbox_storage=OutboxStorage(session),
    )


class FaultGateway(FakePaymentGateway):
    def __init__(self, failures: int, cancel: bool = False) -> None:
        super().__init__()
        self.failures = failures
        self.cancel = cancel

    async def process(self, *, input_dto: ProcessPayment) -> PaymentStatus:
        self.inputs.append(input_dto)
        if self.cancel:
            raise asyncio.CancelledError()
        if len(self.inputs) <= self.failures:
            raise TimeoutError("gateway unavailable")
        return self.status


async def expire_claim(database: DurableDatabase, payment_id: object) -> None:
    async with database.engine.begin() as connection:
        await connection.execute(
            update(PaymentTable)
            .where(
                PaymentTable.id == payment_id,
            )
            .values(lease_until=datetime.now(tz=UTC) - timedelta(seconds=1))
        )


async def test_concurrent_identical_creation_has_one_payment_and_outbox(
    durable_db: DurableDatabase,
) -> None:
    dto = creation("concurrent")
    results = await asyncio.gather(
        create_case(durable_db).execute(input_dto=dto),
        create_case(durable_db).execute(input_dto=dto),
    )
    async with durable_db.engine.connect() as connection:
        counts = (
            await connection.scalar(select(func.count()).select_from(PaymentTable)),
            await connection.scalar(select(func.count()).select_from(OutboxTable)),
        )
    assert (results[0] == results[1], counts) == (True, (1, 1))


@pytest.mark.parametrize(
    "changed",
    [
        {"amount": Decimal("20.50")},
        {"currency": "EUR"},
        {"description": "changed"},
        {"meta_data": {"order": "2"}},
        {"webhook_url": "https://example.invalid/other"},
        {"meta_data": {"order": True}},
    ],
)
async def test_every_changed_creation_field_conflicts(
    durable_db: DurableDatabase,
    changed: dict,
) -> None:
    from dataclasses import replace

    dto = creation("conflict")
    await create_case(durable_db).execute(input_dto=dto)
    with pytest.raises(EntityAlreadyExistsException):
        await create_case(durable_db).execute(input_dto=replace(dto, **changed))


async def test_replay_after_completion_still_returns_original_snapshot(
    durable_db: DurableDatabase,
) -> None:
    dto = creation("completed")
    original = await create_case(durable_db).execute(input_dto=dto)
    await process_case(
        durable_db,
        FakePaymentGateway(),
        FakePaymentWebhookSender(),
    ).execute(input_dto=PaymentAttempt(id=original.payment_id, number=1))
    replay = await create_case(durable_db).execute(input_dto=dto)
    assert replay == original


async def test_concurrent_duplicate_processing_calls_gateway_and_webhook_once(
    durable_db: DurableDatabase,
) -> None:
    accepted = await create_case(durable_db).execute(input_dto=creation("duplicate"))
    gateway = FakePaymentGateway()
    sender = FakePaymentWebhookSender()
    dto = PaymentAttempt(id=accepted.payment_id, number=1)
    results = await asyncio.gather(
        process_case(durable_db, gateway, sender).execute(input_dto=dto),
        process_case(durable_db, gateway, sender).execute(input_dto=dto),
    )
    assert (
        sum(result is not None for result in results),
        len(gateway.inputs),
        len(sender.inputs),
    ) == (1, 1, 1)


async def test_gateway_technical_exhaustion_keeps_business_result_unknown(
    durable_db: DurableDatabase,
) -> None:
    accepted = await create_case(durable_db).execute(input_dto=creation("unknown"))
    gateway = FaultGateway(failures=3)
    sender = FakePaymentWebhookSender()
    for number in (1, 2, 3):
        result = await process_case(durable_db, gateway, sender).execute(
            input_dto=PaymentAttempt(id=accepted.payment_id, number=number),
        )
    assert (
        result.status,
        result.processing_status,
        result.processing_attempts,
        result.notification.status,
        result.notification.webhook_attempts,
        sender.inputs,
    ) == ("pending", "exhausted", 3, "not_sent", 0, [])


async def test_gateway_and_webhook_use_one_shared_budget(
    durable_db: DurableDatabase,
) -> None:
    accepted = await create_case(durable_db).execute(input_dto=creation("shared"))
    gateway = FaultGateway(failures=2)
    sender = FakePaymentWebhookSender()
    sender.exception = TimeoutError("callback unavailable")
    for number in (1, 2, 3):
        result = await process_case(durable_db, gateway, sender).execute(
            input_dto=PaymentAttempt(id=accepted.payment_id, number=number),
        )
    fourth = await process_case(durable_db, gateway, sender).execute(
        input_dto=PaymentAttempt(id=accepted.payment_id, number=4),
    )
    assert (
        result.status,
        result.processing_status,
        result.processing_attempts,
        result.notification.webhook_attempts,
        len(gateway.inputs),
        fourth,
    ) == ("succeeded", "exhausted", 3, 1, 3, None)


async def test_cancelled_start_is_spent_and_recovered_without_double_counting(
    durable_db: DurableDatabase,
) -> None:
    accepted = await create_case(durable_db).execute(input_dto=creation("cancel"))
    sender = FakePaymentWebhookSender()
    cancelled = await asyncio.gather(
        process_case(durable_db, FaultGateway(0, cancel=True), sender).execute(
            input_dto=PaymentAttempt(id=accepted.payment_id, number=1),
        ),
        return_exceptions=True,
    )
    await expire_claim(durable_db, accepted.payment_id)
    recovered = await recover_case(durable_db).execute(
        input_dto=RecoverPaymentAttempt(now=datetime.now(tz=UTC)),
    )
    result = await process_case(durable_db, FakePaymentGateway(), sender).execute(
        input_dto=PaymentAttempt(id=accepted.payment_id, number=2),
    )
    assert (
        isinstance(cancelled[0], asyncio.CancelledError),
        recovered.processing_attempts,
        recovered.processing_status,
        result.processing_attempts,
        result.notification.webhook_attempts,
    ) == (True, 1, "retrying", 2, 1)


async def test_third_crash_recovers_to_dlq_without_fourth_start(
    durable_db: DurableDatabase,
) -> None:
    accepted = await create_case(durable_db).execute(input_dto=creation("last-crash"))
    gateway = FaultGateway(0, cancel=True)
    sender = FakePaymentWebhookSender()
    for number in (1, 2, 3):
        await asyncio.gather(
            process_case(durable_db, gateway, sender).execute(
                input_dto=PaymentAttempt(id=accepted.payment_id, number=number),
            ),
            return_exceptions=True,
        )
        await expire_claim(durable_db, accepted.payment_id)
        recovered = await recover_case(durable_db).execute(
            input_dto=RecoverPaymentAttempt(now=datetime.now(tz=UTC)),
        )
    fourth = await process_case(durable_db, gateway, sender).execute(
        input_dto=PaymentAttempt(id=accepted.payment_id, number=4),
    )
    assert (
        recovered.status,
        recovered.processing_status,
        recovered.processing_attempts,
        recovered.notification.webhook_attempts,
        len(gateway.inputs),
        fourth,
    ) == ("pending", "exhausted", 3, 0, 3, None)


async def test_expired_executor_cannot_write_gateway_result(
    durable_db: DurableDatabase,
) -> None:
    accepted = await create_case(durable_db).execute(input_dto=creation("fencing"))
    old_token = uuid7()
    session = durable_db.sessions()
    storage = PaymentStorage(session)
    async with SqlalchemyUow(session):
        await storage.claim_attempt(
            input_dto=ClaimPaymentAttempt(
                id=accepted.payment_id,
                number=1,
                token=old_token,
                lease_seconds=30,
            )
        )
    await expire_claim(durable_db, accepted.payment_id)
    await recover_case(durable_db).execute(
        input_dto=RecoverPaymentAttempt(now=datetime.now(tz=UTC)),
    )
    async with SqlalchemyUow(session):
        stale_result = await storage.save_gateway_result(
            input_dto=SaveGatewayResult(
                id=accepted.payment_id,
                token=old_token,
                status=PaymentStatus.SUCCEEDED,
                processed_at=datetime.now(tz=UTC),
            )
        )
    assert stale_result is None
