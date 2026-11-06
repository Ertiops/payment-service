from collections.abc import Awaitable, Callable
from decimal import Decimal

from dirty_equals import IsDatetime, IsUUID
from uuid6 import uuid7

from app.adapters.database.storages.payment import PaymentStorage
from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import (
    CreatePayment,
    Payment,
    PaymentCurrency,
    PaymentStatus,
)
from tests.utils.common import now_utc
from tests.utils.payment import initial_notification


async def test__create_if_absent(
    payment_storage: PaymentStorage,
) -> None:
    create_data = CreatePayment(
        amount=Decimal("10.50"),
        currency=PaymentCurrency.USD,
        description="test payment",
        meta_data={"order_id": "order-1"},
        idempotency_key="payment-key",
        webhook_url="https://example.com/webhook",
    )
    payment = await payment_storage.create_if_absent(input_dto=create_data)
    assert payment == Payment(
        id=IsUUID,
        amount=create_data.amount,
        currency=create_data.currency,
        description=create_data.description,
        meta_data=create_data.meta_data,
        status=PaymentStatus.PENDING,
        idempotency_key=create_data.idempotency_key,
        webhook_url=create_data.webhook_url,
        processed_at=None,
        created_at=IsDatetime,
        updated_at=IsDatetime,
        processing_status="ready",
        processing_attempts=0,
        notification=initial_notification(),
    )


async def test__get_by_id(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment()
    payment = await payment_storage.get_by_id(input_dto=db_payment.id)
    assert payment == Payment(
        id=db_payment.id,
        amount=db_payment.amount,
        currency=db_payment.currency,
        description=db_payment.description,
        meta_data=db_payment.meta_data,
        status=db_payment.status,
        idempotency_key=db_payment.idempotency_key,
        webhook_url=db_payment.webhook_url,
        processed_at=db_payment.processed_at,
        created_at=db_payment.created_at,
        updated_at=db_payment.updated_at,
        processing_status="ready",
        processing_attempts=0,
        notification=initial_notification(),
    )


async def test__get_by_id__none(
    payment_storage: PaymentStorage,
) -> None:
    assert await payment_storage.get_by_id(input_dto=uuid7()) is None


async def test__get_by_id__deleted(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment(deleted_at=now_utc())
    assert await payment_storage.get_by_id(input_dto=db_payment.id) is None
