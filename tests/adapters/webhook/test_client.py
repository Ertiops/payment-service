from datetime import UTC, datetime
from ssl import SSLCertVerificationError
from typing import Any, cast

import pytest
from aiohttp import ClientConnectorCertificateError, ClientSession
from uuid6 import uuid7
from yarl import URL

from app.adapters.webhook.client import PaymentWebhookClient
from app.adapters.webhook.config import WebhookConfig
from app.adapters.webhook.handlers import PAYMENT_WEBHOOK_HANDLERS
from app.domain.entities.payment import PaymentStatus
from app.domain.entities.webhook import SendPaymentWebhook


async def test__send_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict[str, Any]] = []
    input_dto = SendPaymentWebhook(
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
        config=WebhookConfig(
            base_url="http://webhook.test",
            timeout_seconds=7,
        ),
    )
    await client.send_once(input_dto=input_dto)
    assert requests == [
        {
            "method": "POST",
            "url": URL("https://example.com/webhook"),
            "handlers": PAYMENT_WEBHOOK_HANDLERS,
            "timeout": 7,
            "json": {
                "payment_id": str(input_dto.payment_id),
                "status": PaymentStatus.SUCCEEDED.value,
                "processed_at": input_dto.processed_at.isoformat(),
            },
        }
    ]


async def test__send__certificate_error_is_not_retried_inline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    input_dto = SendPaymentWebhook(
        payment_id=uuid7(),
        status=PaymentStatus.SUCCEEDED,
        processed_at=datetime(2026, 4, 7, tzinfo=UTC),
        webhook_url="https://example.com/webhook",
    )

    async def send_once(
        self: PaymentWebhookClient,
        *,
        input_dto: SendPaymentWebhook,
    ) -> None:
        nonlocal calls
        calls += 1
        raise ClientConnectorCertificateError(
            None,
            SSLCertVerificationError("certificate verify failed"),
        )

    monkeypatch.setattr(PaymentWebhookClient, "send_once", send_once)
    client = PaymentWebhookClient(
        session=cast(ClientSession, object()),
        config=WebhookConfig(
            base_url="http://webhook.test",
            timeout_seconds=7,
        ),
    )
    certificate_error_raised = False
    try:
        await client.send(input_dto=input_dto)
    except ClientConnectorCertificateError:
        certificate_error_raised = True
    assert (certificate_error_raised, calls) == (True, 1)


async def test__send__success_makes_one_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    input_dto = SendPaymentWebhook(
        payment_id=uuid7(),
        status=PaymentStatus.SUCCEEDED,
        processed_at=datetime(2026, 4, 7, tzinfo=UTC),
        webhook_url="https://example.com/webhook",
    )

    async def send_once(
        self: PaymentWebhookClient,
        *,
        input_dto: SendPaymentWebhook,
    ) -> None:
        nonlocal calls
        calls += 1

    monkeypatch.setattr(PaymentWebhookClient, "send_once", send_once)
    client = PaymentWebhookClient(
        session=cast(ClientSession, object()),
        config=WebhookConfig(
            base_url="http://webhook.test",
            timeout_seconds=7,
        ),
    )
    await client.send(input_dto=input_dto)
    assert calls == 1
