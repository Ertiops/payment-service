from app.application.exceptions import EntityAlreadyExistsException
from app.application.use_case import IUseCase
from app.domain.entities.payment import AcceptedPayment, CreatePayment, GetPaymentByKey
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.payment.workflow import (
    original_accepted_response,
    processing_message,
    same_creation_request,
)


class CreatePaymentUC(IUseCase[CreatePayment, AcceptedPayment]):
    def __init__(
        self,
        uow: AbstractUow,
        payment_storage: IPaymentStorage,
        outbox_storage: IOutboxStorage,
    ) -> None:
        self._payment_storage = payment_storage
        self._outbox_storage = outbox_storage
        self._uow = uow

    async def execute(self, *, input_dto: CreatePayment) -> AcceptedPayment:
        async with self._uow:
            payment = await self._payment_storage.create_if_absent(input_dto=input_dto)
            if payment is None:
                payment = await self._payment_storage.get_by_key(
                    input_dto=GetPaymentByKey(key=input_dto.idempotency_key)
                )
                if payment is None or not same_creation_request(payment, input_dto):
                    raise EntityAlreadyExistsException(
                        "Idempotency key was used with a different request"
                    )
            else:
                await self._outbox_storage.create(
                    input_dto=processing_message(payment.id, 1)
                )
            return original_accepted_response(payment)
