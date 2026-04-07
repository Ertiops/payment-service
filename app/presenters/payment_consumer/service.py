from collections.abc import Mapping
from uuid import UUID

from aiomisc import Service
from dishka import make_async_container
from dishka.async_container import AsyncContainer
from faststream.rabbit import RabbitBroker

from app.adapters.database.di import DatabaseProvider
from app.adapters.payment_gateway.di import PaymentGatewayProvider
from app.adapters.rabbitmq.topology import PAYMENTS_NEW_DLQ, PAYMENTS_NEW_QUEUE
from app.adapters.webhook.di import WebhookProvider
from app.domain.di import PaymentConsumerProvider
from app.domain.entities.payment import ProcessPayment
from app.domain.use_cases.payment.process import ProcessPaymentUC
from app.presenters.payment_consumer.config import PaymentConsumerConfig


class PaymentConsumerService(Service):
    _config: PaymentConsumerConfig
    _broker: RabbitBroker
    _container: AsyncContainer

    def __init__(self, config: PaymentConsumerConfig) -> None:
        super().__init__()
        self._config = config

    async def start(self) -> None:
        self._container = make_async_container(
            DatabaseProvider(
                dsn=self._config.database.dsn,
                debug=self._config.app.debug,
            ),
            PaymentGatewayProvider(config=self._config.payment_gateway),
            WebhookProvider(config=self._config.webhook),
            PaymentConsumerProvider(),
        )
        self._broker = RabbitBroker(self._config.rabbitmq.dsn)
        self._broker.subscriber(PAYMENTS_NEW_QUEUE)(self.consume)
        await self._broker.start()
        await self._broker.declare_queue(PAYMENTS_NEW_DLQ)
        self.start_event.set()

    async def consume(self, message: Mapping[str, str]) -> None:
        async with self._container() as request_container:
            use_case = await request_container.get(ProcessPaymentUC)
            await use_case.execute(
                input_dto=ProcessPayment(
                    id=UUID(message["payment_id"]),
                )
            )

    async def stop(self, exception: Exception | None = None) -> None:
        await self._broker.stop()
        await self._container.close(exception=exception)
