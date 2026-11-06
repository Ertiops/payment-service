from collections.abc import Awaitable, Callable

from httpx import AsyncClient


async def test_identical_post_returns_original_accepted_response(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    headers = {**await create_auth_headers(), "Idempotency-Key": "replay-key"}
    body = {
        "amount": "10.50",
        "currency": "USD",
        "description": "payment",
        "meta_data": {"order_id": "order-1"},
        "webhook_url": "https://example.com/webhook",
    }
    first = await client.post("/api/v1/payments/", headers=headers, json=body)
    replay = await client.post("/api/v1/payments/", headers=headers, json=body)
    assert replay.json() == first.json()


async def test_equivalent_decimal_and_json_object_order_replay(
    client: AsyncClient,
    create_auth_headers: Callable[..., Awaitable[dict[str, str]]],
) -> None:
    headers = {**await create_auth_headers(), "Idempotency-Key": "normalized-key"}
    body = {
        "amount": "10.50",
        "currency": "USD",
        "description": "payment",
        "meta_data": {"a": 1, "b": 2},
        "webhook_url": "https://example.com/webhook",
    }
    await client.post("/api/v1/payments/", headers=headers, json=body)
    replay = await client.post(
        "/api/v1/payments/",
        headers=headers,
        json={**body, "amount": "10.5", "meta_data": {"b": 2, "a": 1}},
    )
    assert replay.status_code == 202
