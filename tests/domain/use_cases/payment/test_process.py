from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.adapters.database.tables import OutboxTable, PaymentTable
from app.domain.entities.payment import PaymentAttempt, PaymentStatus
from app.domain.use_cases.payment.process import ProcessPaymentUC
from tests.plugins.use_cases.payment import FakePaymentGateway, FakePaymentWebhookSender


async def test_process_success(
    process_payment_uc: ProcessPaymentUC,
    payment_gateway: FakePaymentGateway,
    payment_webhook_sender: FakePaymentWebhookSender,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(status=PaymentStatus.PENDING, processed_at=None)
    result = await process_payment_uc.execute(
        input_dto=PaymentAttempt(id=row.id, number=1)
    )
    assert (
        result.status,
        result.processing_status,
        result.processing_attempts,
        result.notification.status,
        result.notification.webhook_attempts,
        len(payment_gateway.inputs),
        [dto.status for dto in payment_webhook_sender.inputs],
    ) == ("succeeded", "completed", 1, "delivered", 1, 1, ["succeeded"])


async def test_business_decline_is_final_and_notifies_client(
    process_payment_uc: ProcessPaymentUC,
    payment_gateway: FakePaymentGateway,
    payment_webhook_sender: FakePaymentWebhookSender,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    payment_gateway.status = PaymentStatus.FAILED
    row = await create_payment(status=PaymentStatus.PENDING, processed_at=None)
    result = await process_payment_uc.execute(
        input_dto=PaymentAttempt(id=row.id, number=1)
    )
    assert (
        result.status,
        result.processing_status,
        [dto.status for dto in payment_webhook_sender.inputs],
    ) == (
        "failed",
        "completed",
        ["failed"],
    )


async def test_missing_payment_is_a_noop(process_payment_uc: ProcessPaymentUC) -> None:
    assert (
        await process_payment_uc.execute(input_dto=PaymentAttempt(id=uuid7(), number=1))
        is None
    )


async def test_known_gateway_result_is_not_processed_again(
    process_payment_uc: ProcessPaymentUC,
    payment_gateway: FakePaymentGateway,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(
        status=PaymentStatus.SUCCEEDED, processed_at=datetime.now(tz=UTC)
    )
    await process_payment_uc.execute(input_dto=PaymentAttempt(id=row.id, number=1))
    assert payment_gateway.inputs == []


async def test_webhook_failure_schedules_one_durable_retry(
    process_payment_uc: ProcessPaymentUC,
    payment_webhook_sender: FakePaymentWebhookSender,
    session: AsyncSession,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    payment_webhook_sender.exception = RuntimeError("webhook failed")
    row = await create_payment(status=PaymentStatus.PENDING, processed_at=None)
    result = await process_payment_uc.execute(
        input_dto=PaymentAttempt(id=row.id, number=1)
    )
    event = await session.scalar(select(OutboxTable))
    assert (
        result.status,
        result.processing_status,
        result.processing_attempts,
        result.notification.status,
        result.notification.webhook_attempts,
        event.event_type,
        event.payload,
    ) == (
        "succeeded",
        "retrying",
        1,
        "retrying",
        1,
        "payments.retry.1",
        {"payment_id": str(row.id), "attempt": 2},
    )


async def test_duplicate_envelope_does_not_send_again(
    process_payment_uc: ProcessPaymentUC,
    payment_gateway: FakePaymentGateway,
    payment_webhook_sender: FakePaymentWebhookSender,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(status=PaymentStatus.PENDING, processed_at=None)
    dto = PaymentAttempt(id=row.id, number=1)
    await process_payment_uc.execute(input_dto=dto)
    replay = await process_payment_uc.execute(input_dto=dto)
    assert (
        replay,
        len(payment_gateway.inputs),
        len(payment_webhook_sender.inputs),
    ) == (
        None,
        1,
        1,
    )


async def test_three_webhook_failures_exhaust_shared_budget(
    process_payment_uc: ProcessPaymentUC,
    payment_gateway: FakePaymentGateway,
    payment_webhook_sender: FakePaymentWebhookSender,
    session: AsyncSession,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    payment_webhook_sender.exception = RuntimeError("unavailable")
    row = await create_payment(status=PaymentStatus.PENDING, processed_at=None)
    for attempt in (1, 2, 3):
        result = await process_payment_uc.execute(
            input_dto=PaymentAttempt(id=row.id, number=attempt)
        )
    fourth = await process_payment_uc.execute(
        input_dto=PaymentAttempt(id=row.id, number=4)
    )
    events = (
        await session.scalars(
            select(OutboxTable).order_by(OutboxTable.created_at, OutboxTable.id)
        )
    ).all()
    assert (
        result.status,
        result.processing_status,
        result.processing_attempts,
        result.notification.webhook_attempts,
        len(payment_gateway.inputs),
        fourth,
        [(event.event_type, event.payload["attempt"]) for event in events],
    ) == (
        "succeeded",
        "exhausted",
        3,
        3,
        1,
        None,
        [("payments.retry.1", 2), ("payments.retry.2", 3), ("payments.new.dlq", 3)],
    )
