from typing import Protocol
from uuid import UUID

from app.domain.entities.payment import CreatePayment, Payment


class IPaymentStorage(Protocol):
    async def create(self, *, input_dto: CreatePayment) -> Payment:
        pass

    async def get_by_id(self, *, input_dto: UUID) -> Payment | None:
        pass
