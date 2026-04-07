from datetime import UTC, datetime

from app.application.exceptions import (
    EntityNotFoundException,
    PaymentProcessingException,
)
from app.application.use_case import IUseCase
from app.domain.entities.payment import (
    Payment,
    PaymentStatus,
    ProcessPayment,
    UpdatePayment,
)
from app.domain.entities.webhook import SendPaymentWebhook
from app.domain.interfaces.gateways.payment import IPaymentGateway
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.interfaces.webhooks.payment import IPaymentWebhookSender
from app.domain.uow import AbstractUow


def create_payment_webhook(input_dto: Payment) -> SendPaymentWebhook:
    if input_dto.processed_at is None:
        raise PaymentProcessingException("Processed payment has no processed_at")
    return SendPaymentWebhook(
        payment_id=input_dto.id,
        status=input_dto.status,
        processed_at=input_dto.processed_at,
        webhook_url=input_dto.webhook_url,
    )


class ProcessPaymentUC(IUseCase[ProcessPayment, Payment | None]):
    def __init__(
        self,
        uow: AbstractUow,
        payment_storage: IPaymentStorage,
        payment_gateway: IPaymentGateway,
        payment_webhook_sender: IPaymentWebhookSender,
    ) -> None:
        self._uow = uow
        self._payment_storage = payment_storage
        self._payment_gateway = payment_gateway
        self._payment_webhook_sender = payment_webhook_sender

    async def execute(self, *, input_dto: ProcessPayment) -> Payment | None:
        async with self._uow:
            payment = await self._payment_storage.get_by_id(input_dto=input_dto.id)
        if payment is None:
            return None
        if payment.status == PaymentStatus.PENDING:
            status = await self._payment_gateway.process(input_dto=input_dto)
            async with self._uow:
                try:
                    payment = await self._payment_storage.update_by_id(
                        input_dto=UpdatePayment(
                            id=input_dto.id,
                            status=status,
                            processed_at=datetime.now(tz=UTC),
                        )
                    )
                except EntityNotFoundException:
                    return None
        await self._payment_webhook_sender.send(
            input_dto=create_payment_webhook(input_dto=payment)
        )
        return payment
