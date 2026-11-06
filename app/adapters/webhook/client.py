from typing import ClassVar

from aiohttp import ClientSession
from asyncly import BaseHttpClient, TimeoutType
from yarl import URL

from app.adapters.webhook.config import WebhookConfig
from app.adapters.webhook.handlers import PAYMENT_WEBHOOK_HANDLERS
from app.domain.entities.webhook import SendPaymentWebhook
from app.domain.interfaces.webhooks.payment import IPaymentWebhookSender


class PaymentWebhookClient(BaseHttpClient, IPaymentWebhookSender):
    DEFAULT_TIMEOUT: ClassVar[TimeoutType] = 5

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
        await self.send_once(input_dto=input_dto)

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
