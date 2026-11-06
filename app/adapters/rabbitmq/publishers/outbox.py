from aio_pika.exceptions import AMQPException
from faststream.exceptions import FastStreamException
from faststream.rabbit import RabbitBroker
from pamqp.commands import Basic

from app.adapters.rabbitmq.config import RabbitMQConfig
from app.adapters.rabbitmq.topology import payment_queues
from app.application.exceptions import OutboxPublishException
from app.domain.entities.outbox import PublishOutboxMessage
from app.domain.interfaces.publishers.outbox import IOutboxPublisher


class RabbitMQOutboxPublisher(IOutboxPublisher):
    def __init__(self, broker: RabbitBroker, config: RabbitMQConfig) -> None:
        self._broker = broker
        self._config = config
        self._queues = payment_queues(config.retry_delay_seconds)

    async def publish(self, *, input_dto: PublishOutboxMessage) -> None:
        try:
            confirmation = await self._broker.publish(
                message=dict(input_dto.payload),
                queue=self._queues[input_dto.event_type],
                message_id=str(input_dto.id),
                persist=True,
                mandatory=True,
                timeout=self._config.publish_timeout_seconds,
            )
            if not isinstance(confirmation, Basic.Ack):
                raise OutboxPublishException("Broker did not confirm publication")
        except (AMQPException, FastStreamException, TimeoutError, OSError) as exc:
            raise OutboxPublishException(type(exc).__name__) from exc
