from collections.abc import Awaitable, Callable

import pytest
from uuid6 import uuid7

from app.adapters.database.tables import PaymentTable
from app.application.exceptions import EntityNotFoundException
from app.domain.entities.payment import Payment
from app.domain.use_cases.payment.get_by_id import GetPaymentByIdUC
from tests.utils.common import now_utc


async def test__get_by_id(
    get_payment_by_id_uc: GetPaymentByIdUC,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment()
    payment = await get_payment_by_id_uc.execute(input_dto=db_payment.id)
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
    )


async def test__get_by_id__entity_not_found_exception(
    get_payment_by_id_uc: GetPaymentByIdUC,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await get_payment_by_id_uc.execute(input_dto=uuid7())


async def test__get_by_id__entity_not_found_exception__deleted(
    get_payment_by_id_uc: GetPaymentByIdUC,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment(deleted_at=now_utc())
    with pytest.raises(EntityNotFoundException):
        await get_payment_by_id_uc.execute(input_dto=db_payment.id)
