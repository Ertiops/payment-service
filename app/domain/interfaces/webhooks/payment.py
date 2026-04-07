from typing import Protocol

from app.domain.entities.webhook import SendPaymentWebhook


class IPaymentWebhookSender(Protocol):
    async def send(self, *, input_dto: SendPaymentWebhook) -> None:
        pass
