from collections.abc import AsyncIterator

from aiohttp import ClientSession
from dishka import Provider, Scope, provide

from app.adapters.webhook.client import PaymentWebhookClient
from app.adapters.webhook.config import WebhookConfig
from app.domain.interfaces.webhooks.payment import IPaymentWebhookSender


class WebhookProvider(Provider):
    def __init__(self, config: WebhookConfig) -> None:
        super().__init__()
        self._config = config

    @provide(scope=Scope.APP)
    async def session(self) -> AsyncIterator[ClientSession]:
        async with ClientSession() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def payment_webhook_sender(self, session: ClientSession) -> IPaymentWebhookSender:
        return PaymentWebhookClient(
            session=session,
            config=self._config,
        )
