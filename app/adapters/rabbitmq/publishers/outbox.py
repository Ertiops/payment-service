from aio_pika.exceptions import AMQPException
from faststream.exceptions import FastStreamException
from faststream.rabbit import RabbitBroker

from app.adapters.rabbitmq.topology import PAYMENTS_NEW_QUEUE
from app.application.exceptions import OutboxPublishException
from app.domain.entities.outbox import PublishOutboxMessage
from app.domain.interfaces.publishers.outbox import IOutboxPublisher


class RabbitMQOutboxPublisher(IOutboxPublisher):
    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    async def publish(self, *, input_dto: PublishOutboxMessage) -> None:
        try:
            await self._broker.publish(
                message=dict(input_dto.payload),
                queue=PAYMENTS_NEW_QUEUE,
                message_id=str(input_dto.id),
                persist=True,
            )
        except (AMQPException, FastStreamException) as e:
            raise OutboxPublishException(str(e)) from e
