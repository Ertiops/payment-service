import socket
from datetime import UTC, datetime

import pytest
from aiohttp import ClientSession, web
from uuid6 import uuid7

from app.adapters.webhook.client import PaymentWebhookClient
from app.adapters.webhook.config import WebhookConfig
from app.application.exceptions import WebhookDeliveryException
from app.domain.entities.payment import PaymentStatus
from app.domain.entities.webhook import SendPaymentWebhook


@pytest.mark.parametrize("status", [302, 307])
async def test_redirect_is_one_failed_attempt_without_following_target(
    status: int,
) -> None:
    requests: list[str] = []

    async def source(request: web.Request) -> web.Response:
        requests.append("source:" + request.method)
        return web.Response(status=status, headers={"Location": "/target"})

    async def target(request: web.Request) -> web.Response:
        requests.append("target:" + request.method)
        return web.Response(status=200)

    app = web.Application()
    app.router.add_route("*", "/source", source)
    app.router.add_route("*", "/target", target)
    runner = web.AppRunner(app)
    await runner.setup()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    site = web.SockSite(runner, listener)
    await site.start()
    failed = False
    try:
        async with ClientSession() as session:
            client = PaymentWebhookClient(
                session=session,
                config=WebhookConfig(timeout_seconds=2),
            )
            try:
                await client.send(
                    input_dto=SendPaymentWebhook(
                        payment_id=uuid7(),
                        status=PaymentStatus.SUCCEEDED,
                        processed_at=datetime.now(tz=UTC),
                        webhook_url=f"http://127.0.0.1:{port}/source",
                    )
                )
            except WebhookDeliveryException:
                failed = True
    finally:
        await runner.cleanup()
    assert (failed, requests) == (True, ["source:POST"])
