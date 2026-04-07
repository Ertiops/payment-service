from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import uuid4

from httpx import AsyncClient

from app.presenters.rest.routers.api.v1.schemas.payment import PaymentSchema
from tests.plugins.factories.payment import PaymentTable


async def test__get_by_id__unauthorized__status(
    client: AsyncClient,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment()
    response = await client.get(
        f"/api/v1/payments/{db_payment.id}/",
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test__get_by_id__forbidden__status(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment()
    response = await client.get(
        f"/api/v1/payments/{db_payment.id}/",
        headers=await create_auth_headers(secret="wrong_secret"),
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test__get_by_id__ok__status(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment()
    response = await client.get(
        f"/api/v1/payments/{db_payment.id}/",
        headers=await create_auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK


async def test__get_by_id__ok__response(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment()
    response = await client.get(
        f"/api/v1/payments/{db_payment.id}/",
        headers=await create_auth_headers(),
    )
    assert response.json() == PaymentSchema.model_validate(db_payment).model_dump(
        mode="json"
    )


async def test__get_by_id__not_found__status(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    response = await client.get(
        f"/api/v1/payments/{uuid4()}/",
        headers=await create_auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
