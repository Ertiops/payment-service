from typing import Protocol

from app.domain.entities.payment import PaymentStatus, ProcessPayment


class IPaymentGateway(Protocol):
    async def process(self, *, input_dto: ProcessPayment) -> PaymentStatus:
        pass
