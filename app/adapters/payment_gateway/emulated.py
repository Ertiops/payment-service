import asyncio
from random import Random

from app.adapters.payment_gateway.config import PaymentGatewayConfig
from app.domain.entities.payment import PaymentStatus, ProcessPayment
from app.domain.interfaces.gateways.payment import IPaymentGateway


class EmulatedPaymentGateway(IPaymentGateway):
    def __init__(self, config: PaymentGatewayConfig) -> None:
        self._config = config
        self._random = Random()

    async def process(self, *, input_dto: ProcessPayment) -> PaymentStatus:
        await asyncio.sleep(
            self._random.uniform(
                self._config.min_delay_seconds,
                self._config.max_delay_seconds,
            )
        )
        if self._random.random() <= self._config.success_rate:
            return PaymentStatus.SUCCEEDED
        return PaymentStatus.FAILED
