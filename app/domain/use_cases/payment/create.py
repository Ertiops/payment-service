from app.application.use_case import IUseCase
from app.domain.entities.payment import CreatePayment, Payment
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.uow import AbstractUow


class CreatePaymentUC(IUseCase[CreatePayment, Payment]):
    def __init__(
        self,
        uow: AbstractUow,
        payment_storage: IPaymentStorage,
    ) -> None:
        self._payment_storage = payment_storage
        self._uow = uow

    async def execute(self, *, input_dto: CreatePayment) -> Payment:
        async with self._uow:
            return await self._payment_storage.create(input_dto=input_dto)
