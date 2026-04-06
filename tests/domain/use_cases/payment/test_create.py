from collections.abc import Awaitable, Callable
from decimal import Decimal

import pytest
from dirty_equals import IsDatetime, IsUUID

from app.adapters.database.tables import PaymentTable
from app.application.exceptions import EntityAlreadyExistsException
from app.domain.entities.payment import (
    CreatePayment,
    Payment,
    PaymentCurrency,
    PaymentStatus,
)
from app.domain.use_cases.payment.create import CreatePaymentUC


async def test__create(
    create_payment_uc: CreatePaymentUC,
) -> None:
    input_dto = CreatePayment(
        amount=Decimal("10.50"),
        currency=PaymentCurrency.USD,
        description="test payment",
        meta_data={"order_id": "order-1"},
        status=PaymentStatus.PENDING,
        idempotency_key="payment-key",
        webhook_url="https://example.com/webhook",
    )
    payment = await create_payment_uc.execute(input_dto=input_dto)
    assert payment == Payment(
        id=IsUUID,
        amount=input_dto.amount,
        currency=input_dto.currency,
        description=input_dto.description,
        meta_data=input_dto.meta_data,
        status=input_dto.status,
        idempotency_key=input_dto.idempotency_key,
        webhook_url=input_dto.webhook_url,
        processed_at=None,
        created_at=IsDatetime,
        updated_at=IsDatetime,
    )


async def test__create__entity_already_exists_exception__idempotency_key(
    create_payment_uc: CreatePaymentUC,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment(idempotency_key="payment-key")
    with pytest.raises(EntityAlreadyExistsException):
        await create_payment_uc.execute(
            input_dto=CreatePayment(
                amount=Decimal("10.50"),
                currency=PaymentCurrency.USD,
                description="test payment",
                meta_data={"order_id": "order-1"},
                status=PaymentStatus.PENDING,
                idempotency_key=db_payment.idempotency_key,
                webhook_url="https://example.com/webhook",
            )
        )
