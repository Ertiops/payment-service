from app.application.use_case import IUseCase
from app.domain.entities.outbox import CreateOutbox, OutboxEventType, OutboxStatus
from app.domain.entities.payment import (
    CreatePayment,
    Payment,
)
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.uow import AbstractUow


class CreatePaymentUC(IUseCase[CreatePayment, Payment]):
    def __init__(
        self,
        uow: AbstractUow,
        payment_storage: IPaymentStorage,
        outbox_storage: IOutboxStorage,
    ) -> None:
        self._payment_storage = payment_storage
        self._outbox_storage = outbox_storage
        self._uow = uow

    async def execute(self, *, input_dto: CreatePayment) -> Payment:
        async with self._uow:
            payment = await self._payment_storage.create(input_dto=input_dto)
            await self._outbox_storage.create(
                input_dto=CreateOutbox(
                    event_type=OutboxEventType.PAYMENT_CREATED,
                    payload={"payment_id": str(payment.id)},
                    status=OutboxStatus.PENDING,
                    attempts=0,
                    last_error=None,
                    published_at=None,
                )
            )
            return payment
