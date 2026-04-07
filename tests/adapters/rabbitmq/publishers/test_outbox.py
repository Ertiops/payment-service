from typing import Any

from faststream.rabbit import RabbitBroker, TestRabbitBroker
from uuid6 import uuid7

from app.adapters.rabbitmq.publishers.outbox import RabbitMQOutboxPublisher
from app.adapters.rabbitmq.topology import PAYMENTS_NEW_QUEUE
from app.domain.entities.outbox import OutboxEventType, PublishOutboxMessage


async def test__publish() -> None:
    broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
    messages: list[dict[str, Any]] = []

    @broker.subscriber(PAYMENTS_NEW_QUEUE)
    async def handle(message: dict[str, Any]) -> None:
        messages.append(message)

    async with TestRabbitBroker(broker, connect_only=False):
        publisher = RabbitMQOutboxPublisher(broker=broker)
        await publisher.publish(
            input_dto=PublishOutboxMessage(
                id=uuid7(),
                event_type=OutboxEventType.PAYMENT_CREATED,
                payload={"payment_id": "payment-id"},
            )
        )

    assert messages == [{"payment_id": "payment-id"}]
