from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import UUID

from dirty_equals import IsStr
from httpx import AsyncClient
from uuid6 import uuid7

from app.adapters.database.tables import PaymentTable


def api_url(payment_id: UUID = uuid7()) -> str:
    return f"/api/v1/payments/{payment_id}/"


async def test__get_by_id__not_found__status(client: AsyncClient) -> None:
    response = await client.get(api_url())
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test__get_by_id__ok__status(
    create_payment: Callable[..., Awaitable[PaymentTable]],
    client: AsyncClient,
) -> None:
    db_payment = await create_payment()
    response = await client.get(api_url(db_payment.id))
    assert response.status_code == HTTPStatus.OK


async def test__get_by_id__ok__format(
    create_payment: Callable[..., Awaitable[PaymentTable]],
    client: AsyncClient,
) -> None:
    db_payment = await create_payment()
    response = await client.get(api_url(db_payment.id))
    assert response.json() == dict(
        id=str(db_payment.id),
        amount=str(db_payment.amount),
        currency=db_payment.currency,
        description=db_payment.description,
        meta_data=db_payment.meta_data,
        status=db_payment.status,
        idempotency_key=db_payment.idempotency_key,
        webhook_url=db_payment.webhook_url,
        processed_at=IsStr | None,
        created_at=IsStr,
        updated_at=IsStr,
    )
