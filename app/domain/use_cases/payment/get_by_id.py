from uuid import UUID

from app.application.exceptions import EntityNotFoundException
from app.application.use_case import IUseCase
from app.domain.entities.payment import Payment
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.uow import AbstractUow


class GetPaymentByIdUC(IUseCase[UUID, Payment]):
    def __init__(
        self,
        uow: AbstractUow,
        payment_storage: IPaymentStorage,
    ) -> None:
        self._payment_storage = payment_storage
        self._uow = uow

    async def execute(self, *, input_dto: UUID) -> Payment:
        async with self._uow:
            payment = await self._payment_storage.get_by_id(input_dto=input_dto)
            if payment is None:
                raise EntityNotFoundException(entity=Payment, entity_id=input_dto)
            return payment
