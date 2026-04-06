from collections.abc import Awaitable, Callable, Mapping
from http import HTTPStatus
from typing import Any

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import PaymentCurrency, PaymentStatus

API_URL = "/api/v1/payments/"


@pytest.mark.parametrize(
    "body",
    (
        dict(
            amount="0",
            currency=PaymentCurrency.USD,
            description="test payment",
            meta_data={"order_id": "order-1"},
            webhook_url="https://example.com/webhook",
        ),
        dict(
            amount="10.50",
            currency="GBP",
            description="test payment",
            meta_data={"order_id": "order-1"},
            webhook_url="https://example.com/webhook",
        ),
        dict(
            amount="10.50",
            currency=PaymentCurrency.USD,
            description="",
            meta_data={"order_id": "order-1"},
            webhook_url="https://example.com/webhook",
        ),
        dict(
            amount="10.50",
            currency=PaymentCurrency.USD,
            description="test payment",
            meta_data="test",
            webhook_url="https://example.com/webhook",
        ),
        dict(
            amount="10.50",
            currency=PaymentCurrency.USD,
            description="test payment",
            meta_data={"order_id": "order-1"},
            webhook_url="test",
        ),
    ),
)
async def test__create__unprocessable_entity(
    client: AsyncClient,
    body: Mapping[str, Any],
) -> None:
    response = await client.post(
        API_URL,
        headers={"Idempotency-Key": "payment-key"},
        json=body,
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__create__unprocessable_entity__idempotency_key(
    client: AsyncClient,
) -> None:
    response = await client.post(
        API_URL,
        json=dict(
            amount="10.50",
            currency=PaymentCurrency.USD,
            description="test payment",
            meta_data={"order_id": "order-1"},
            webhook_url="https://example.com/webhook",
        ),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__create__ok__status(client: AsyncClient) -> None:
    response = await client.post(
        API_URL,
        headers={"Idempotency-Key": "payment-key"},
        json=dict(
            amount="10.50",
            currency=PaymentCurrency.USD,
            description="test payment",
            meta_data={"order_id": "order-1"},
            webhook_url="https://example.com/webhook",
        ),
    )
    assert response.status_code == HTTPStatus.ACCEPTED


async def test__create__ok__format(client: AsyncClient) -> None:
    response = await client.post(
        API_URL,
        headers={"Idempotency-Key": "payment-key"},
        json=dict(
            amount="10.50",
            currency=PaymentCurrency.USD,
            description="test payment",
            meta_data={"order_id": "order-1"},
            webhook_url="https://example.com/webhook",
        ),
    )
    assert response.json() == dict(
        payment_id=IsStr,
        status=PaymentStatus.PENDING,
        created_at=IsStr,
    )


async def test__create__conflict__duplicate__idempotency_key(
    client: AsyncClient,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    db_payment = await create_payment(idempotency_key="payment-key")
    response = await client.post(
        API_URL,
        headers={"Idempotency-Key": db_payment.idempotency_key},
        json=dict(
            amount="10.50",
            currency=PaymentCurrency.USD,
            description="test payment",
            meta_data={"order_id": "order-1"},
            webhook_url="https://example.com/webhook",
        ),
    )
    assert response.status_code == HTTPStatus.CONFLICT
