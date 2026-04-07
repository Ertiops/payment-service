from collections.abc import Awaitable, Callable
from http import HTTPStatus

from httpx import AsyncClient

from app.domain.entities.payment import PaymentCurrency, PaymentStatus
from app.presenters.rest.routers.api.v1.schemas.payment import PaymentAcceptedSchema
from tests.plugins.factories.payment import PaymentTable

API_URL = "/api/v1/payments/"


async def test__create__unauthorized__status(
    client: AsyncClient,
) -> None:
    response = await client.post(
        API_URL,
        headers={
            "Idempotency-Key": "payment-key",
        },
        json={
            "amount": "10.50",
            "currency": PaymentCurrency.USD,
            "description": "test payment",
            "meta_data": {"order_id": "order-1"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test__create__forbidden__status(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    response = await client.post(
        API_URL,
        headers={
            **await create_auth_headers(secret="wrong_secret"),
            "Idempotency-Key": "payment-key",
        },
        json={
            "amount": "10.50",
            "currency": PaymentCurrency.USD,
            "description": "test payment",
            "meta_data": {"order_id": "order-1"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test__create__ok__status(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    response = await client.post(
        API_URL,
        headers={
            **await create_auth_headers(),
            "Idempotency-Key": "payment-key",
        },
        json={
            "amount": "10.50",
            "currency": PaymentCurrency.USD,
            "description": "test payment",
            "meta_data": {"order_id": "order-1"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert response.status_code == HTTPStatus.ACCEPTED


async def test__create__ok__response(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    response = await client.post(
        API_URL,
        headers={
            **await create_auth_headers(),
            "Idempotency-Key": "payment-key",
        },
        json={
            "amount": "10.50",
            "currency": PaymentCurrency.USD,
            "description": "test payment",
            "meta_data": {"order_id": "order-1"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert (
        PaymentAcceptedSchema.model_validate(response.json()).status
        == PaymentStatus.PENDING
    )


async def test__create__validation_error__status(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    response = await client.post(
        API_URL,
        headers={
            **await create_auth_headers(),
            "Idempotency-Key": "payment-key",
        },
        json={
            "amount": "0",
            "currency": PaymentCurrency.USD,
            "description": "test payment",
            "meta_data": {"order_id": "order-1"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__create__missing_idempotency_key__status(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    response = await client.post(
        API_URL,
        headers=await create_auth_headers(),
        json={
            "amount": "10.50",
            "currency": PaymentCurrency.USD,
            "description": "test payment",
            "meta_data": {"order_id": "order-1"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__create__conflict__duplicate__idempotency_key(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment(idempotency_key="payment-key")
    response = await client.post(
        API_URL,
        headers={
            **await create_auth_headers(),
            "Idempotency-Key": db_payment.idempotency_key,
        },
        json={
            "amount": "10.50",
            "currency": PaymentCurrency.USD,
            "description": "test payment",
            "meta_data": {"order_id": "order-1"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
