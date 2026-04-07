from typing import ClassVar

from aiohttp import ClientConnectorCertificateError, ClientError, ClientSession
from aiomisc import asyncretry
from asyncly import BaseHttpClient, TimeoutType
from yarl import URL

from app.adapters.webhook.config import WebhookConfig
from app.adapters.webhook.handlers import PAYMENT_WEBHOOK_HANDLERS
from app.application.exceptions import WebhookDeliveryException
from app.domain.entities.webhook import SendPaymentWebhook
from app.domain.interfaces.webhooks.payment import IPaymentWebhookSender


class PaymentWebhookClient(BaseHttpClient, IPaymentWebhookSender):
    DEFAULT_TIMEOUT: ClassVar[TimeoutType] = 5
    RETRY_EXCEPTIONS: ClassVar[tuple[type[Exception], ...]] = (
        ClientConnectorCertificateError,
        ClientError,
        TimeoutError,
        WebhookDeliveryException,
    )

    def __init__(
        self,
        session: ClientSession,
        config: WebhookConfig,
    ) -> None:
        super().__init__(
            url=config.base_url,
            session=session,
            client_name="payment_webhook",
        )
        self._config = config

    async def send(self, *, input_dto: SendPaymentWebhook) -> None:
        @asyncretry(
            max_tries=self._config.max_attempts,
            exceptions=self.RETRY_EXCEPTIONS,
            pause=self._config.initial_delay_seconds,
        )
        async def send_with_retry() -> None:
            await self.send_once(input_dto=input_dto)

        await send_with_retry()

    async def send_once(self, *, input_dto: SendPaymentWebhook) -> None:
        await self._make_req(
            method="POST",
            url=URL(input_dto.webhook_url),
            handlers=PAYMENT_WEBHOOK_HANDLERS,
            timeout=self._config.timeout_seconds,
            json={
                "payment_id": str(input_dto.payment_id),
                "status": input_dto.status.value,
                "processed_at": input_dto.processed_at.isoformat(),
            },
        )
