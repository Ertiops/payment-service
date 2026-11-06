from datetime import UTC, datetime
from ssl import SSLCertVerificationError
from typing import Any, cast

import pytest
from aiohttp import ClientConnectorCertificateError, ClientError, ClientSession
from uuid6 import uuid7
from yarl import URL

from app.adapters.webhook.client import PaymentWebhookClient
from app.adapters.webhook.config import WebhookConfig
from app.adapters.webhook.handlers import PAYMENT_WEBHOOK_HANDLERS
from app.application.exceptions import WebhookDeliveryException
from app.domain.entities.payment import PaymentStatus
from app.domain.entities.webhook import SendPaymentWebhook


async def test_send_performs_one_post_without_following_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict[str, Any]] = []
    dto = SendPaymentWebhook(
        payment_id=uuid7(),
        status=PaymentStatus.SUCCEEDED,
        processed_at=datetime(2026, 4, 7, tzinfo=UTC),
        webhook_url="https://example.com/webhook",
    )

    async def make_req(self: PaymentWebhookClient, **kwargs: Any) -> None:
        requests.append(kwargs)

    monkeypatch.setattr(PaymentWebhookClient, "_make_req", make_req)
    client = PaymentWebhookClient(
        session=cast(ClientSession, object()),
        config=WebhookConfig(timeout_seconds=7),
    )
    await client.send(input_dto=dto)
    assert requests == [
        {
            "method": "POST",
            "url": URL(dto.webhook_url),
            "handlers": PAYMENT_WEBHOOK_HANDLERS,
            "timeout": 7,
            "allow_redirects": False,
            "json": {
                "payment_id": str(dto.payment_id),
                "status": "succeeded",
                "processed_at": dto.processed_at.isoformat(),
            },
        }
    ]


@pytest.mark.parametrize(
    "error",
    [
        WebhookDeliveryException("non-2xx"),
        TimeoutError("timeout"),
        ClientConnectorCertificateError(None, SSLCertVerificationError("certificate")),
    ],
)
async def test_failure_is_not_retried_inside_http_adapter(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> None:
    calls = 0

    async def make_req(self: PaymentWebhookClient, **kwargs: Any) -> None:
        nonlocal calls
        calls += 1
        raise error

    monkeypatch.setattr(PaymentWebhookClient, "_make_req", make_req)
    client = PaymentWebhookClient(
        session=cast(ClientSession, object()),
        config=WebhookConfig(),
    )
    failed = False
    try:
        await client.send(
            input_dto=SendPaymentWebhook(
                payment_id=uuid7(),
                status=PaymentStatus.SUCCEEDED,
                processed_at=datetime.now(tz=UTC),
                webhook_url="https://example.invalid/webhook",
            )
        )
    except (ClientError, TimeoutError, WebhookDeliveryException):
        failed = True
    assert (failed, calls) == (True, 1)
