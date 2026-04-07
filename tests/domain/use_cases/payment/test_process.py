from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import pytest
from dirty_equals import IsDatetime
from uuid6 import uuid7

from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import (
    Payment,
    PaymentStatus,
    ProcessPayment,
)
from app.domain.entities.webhook import SendPaymentWebhook
from app.domain.use_cases.payment.process import ProcessPaymentUC
from tests.plugins.use_cases.payment import FakePaymentGateway, FakePaymentWebhookSender


async def test__process(
    process_payment_uc: ProcessPaymentUC,
    payment_webhook_sender: FakePaymentWebhookSender,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment(
        status=PaymentStatus.PENDING,
        processed_at=None,
    )
    payment = await process_payment_uc.execute(
        input_dto=ProcessPayment(id=db_payment.id)
    )
    assert (payment, payment_webhook_sender.inputs) == (
        Payment(
            id=db_payment.id,
            amount=db_payment.amount,
            currency=db_payment.currency,
            description=db_payment.description,
            meta_data=db_payment.meta_data,
            status=PaymentStatus.SUCCEEDED,
            idempotency_key=db_payment.idempotency_key,
            webhook_url=db_payment.webhook_url,
            processed_at=IsDatetime,
            created_at=db_payment.created_at,
            updated_at=IsDatetime,
        ),
        [
            SendPaymentWebhook(
                payment_id=db_payment.id,
                status=PaymentStatus.SUCCEEDED,
                processed_at=IsDatetime,
                webhook_url=db_payment.webhook_url,
            )
        ],
    )


async def test__process__failed(
    process_payment_uc: ProcessPaymentUC,
    payment_gateway: FakePaymentGateway,
    payment_webhook_sender: FakePaymentWebhookSender,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    payment_gateway.status = PaymentStatus.FAILED
    db_payment = await create_payment(
        status=PaymentStatus.PENDING,
        processed_at=None,
    )
    payment = await process_payment_uc.execute(
        input_dto=ProcessPayment(id=db_payment.id)
    )
    assert (payment, payment_webhook_sender.inputs) == (
        Payment(
            id=db_payment.id,
            amount=db_payment.amount,
            currency=db_payment.currency,
            description=db_payment.description,
            meta_data=db_payment.meta_data,
            status=PaymentStatus.FAILED,
            idempotency_key=db_payment.idempotency_key,
            webhook_url=db_payment.webhook_url,
            processed_at=IsDatetime,
            created_at=db_payment.created_at,
            updated_at=IsDatetime,
        ),
        [
            SendPaymentWebhook(
                payment_id=db_payment.id,
                status=PaymentStatus.FAILED,
                processed_at=IsDatetime,
                webhook_url=db_payment.webhook_url,
            )
        ],
    )


async def test__process__none__not_found(
    process_payment_uc: ProcessPaymentUC,
) -> None:
    assert (
        await process_payment_uc.execute(input_dto=ProcessPayment(id=uuid7())) is None
    )


async def test__process__already_processed(
    process_payment_uc: ProcessPaymentUC,
    payment_gateway: FakePaymentGateway,
    payment_webhook_sender: FakePaymentWebhookSender,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment(
        status=PaymentStatus.SUCCEEDED,
        processed_at=datetime.now(tz=UTC),
    )
    payment_gateway.status = PaymentStatus.FAILED
    payment = await process_payment_uc.execute(
        input_dto=ProcessPayment(id=db_payment.id)
    )
    assert (payment, payment_gateway.inputs, payment_webhook_sender.inputs) == (
        Payment(
            id=db_payment.id,
            amount=db_payment.amount,
            currency=db_payment.currency,
            description=db_payment.description,
            meta_data=db_payment.meta_data,
            status=PaymentStatus.SUCCEEDED,
            idempotency_key=db_payment.idempotency_key,
            webhook_url=db_payment.webhook_url,
            processed_at=IsDatetime,
            created_at=db_payment.created_at,
            updated_at=IsDatetime,
        ),
        [],
        [
            SendPaymentWebhook(
                payment_id=db_payment.id,
                status=PaymentStatus.SUCCEEDED,
                processed_at=IsDatetime,
                webhook_url=db_payment.webhook_url,
            )
        ],
    )


async def test__process__webhook_exception(
    process_payment_uc: ProcessPaymentUC,
    payment_webhook_sender: FakePaymentWebhookSender,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    payment_webhook_sender.exception = RuntimeError("webhook failed")
    db_payment = await create_payment(
        status=PaymentStatus.PENDING,
        processed_at=None,
    )
    with pytest.raises(RuntimeError):
        await process_payment_uc.execute(input_dto=ProcessPayment(id=db_payment.id))
