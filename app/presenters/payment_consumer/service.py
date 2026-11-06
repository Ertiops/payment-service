import asyncio
import logging
from typing import Any

from aiomisc import Service
from dishka import make_async_container
from dishka.async_container import AsyncContainer
from faststream.exceptions import RejectMessage
from faststream.middlewares import AckPolicy
from faststream.rabbit import RabbitBroker
from faststream.rabbit.schemas.channel import Channel
from pydantic import ValidationError

from app.adapters.database.di import DatabaseProvider
from app.adapters.payment_gateway.di import PaymentGatewayProvider
from app.adapters.rabbitmq.topology import declare_payment_topology, payment_queues
from app.adapters.webhook.di import WebhookProvider
from app.domain.di import PaymentConsumerProvider
from app.domain.entities.outbox import OutboxEventType
from app.domain.entities.payment import PaymentAttempt
from app.domain.use_cases.payment.process import ProcessPaymentUC
from app.presenters.payment_consumer.config import PaymentConsumerConfig
from app.presenters.payment_consumer.schemas import (
    PaymentMessageSchema,
    decode_payment_message,
)

log = logging.getLogger(__name__)


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
            PaymentConsumerProvider(config=self._config.processing),
        )
        self._broker = RabbitBroker(
            self._config.rabbitmq.dsn,
            default_channel=Channel(prefetch_count=1),
        )
        await self._broker.connect()
        await declare_payment_topology(self._broker, self._config.rabbitmq)
        queue = payment_queues(self._config.rabbitmq.retry_delay_seconds)[
            OutboxEventType.PAYMENT_CREATED
        ]
        self._broker.subscriber(
            queue, ack_policy=AckPolicy.NACK_ON_ERROR, decoder=decode_payment_message
        )(self.consume)
        await self._broker.start()
        self.start_event.set()

    async def consume(self, message: Any) -> None:
        try:
            envelope = PaymentMessageSchema.model_validate(message)
        except ValidationError as exc:
            log.warning("Rejecting malformed payment envelope")
            raise RejectMessage() from exc
        try:
            async with self._container() as request_container:
                use_case = await request_container.get(ProcessPaymentUC)
                await use_case.execute(
                    input_dto=PaymentAttempt(
                        id=envelope.payment_id,
                        number=envelope.attempt,
                    )
                )
        except Exception:
            log.exception(
                "Payment infrastructure failure; message remains unacknowledged"
            )
            await asyncio.sleep(1)
            raise

    async def stop(self, exception: Exception | None = None) -> None:
        await self._broker.stop()
        await self._container.close(exception=exception)
