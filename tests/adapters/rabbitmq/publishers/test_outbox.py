from unittest.mock import AsyncMock

import pytest
from faststream.rabbit import RabbitBroker
from pamqp.commands import Basic
from uuid6 import uuid7

from app.adapters.rabbitmq.config import RabbitMQConfig
from app.adapters.rabbitmq.publishers.outbox import RabbitMQOutboxPublisher
from app.adapters.rabbitmq.topology import PAYMENTS_NEW_QUEUE
from app.application.exceptions import OutboxPublishException
from app.domain.entities.outbox import OutboxEventType, PublishOutboxMessage


async def test_confirmed_publication_preserves_envelope_and_delivery_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
    publish = AsyncMock(return_value=Basic.Ack())
    monkeypatch.setattr(broker, "publish", publish)
    dto = PublishOutboxMessage(
        id=uuid7(),
        event_type=OutboxEventType.PAYMENT_CREATED,
        payload={"payment_id": "payment-id", "attempt": 1},
    )
    publisher = RabbitMQOutboxPublisher(
        broker=broker,
        config=RabbitMQConfig(dsn="amqp://unused"),
    )
    await publisher.publish(input_dto=dto)
    assert publish.await_args.kwargs == {
        "message": dict(dto.payload),
        "queue": PAYMENTS_NEW_QUEUE,
        "message_id": str(dto.id),
        "persist": True,
        "mandatory": True,
        "timeout": 5,
    }


async def test_unconfirmed_publication_is_not_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
    monkeypatch.setattr(broker, "publish", AsyncMock(return_value=None))
    publisher = RabbitMQOutboxPublisher(
        broker=broker,
        config=RabbitMQConfig(dsn="amqp://unused"),
    )
    with pytest.raises(OutboxPublishException):
        await publisher.publish(
            input_dto=PublishOutboxMessage(
                id=uuid7(),
                event_type=OutboxEventType.PAYMENT_CREATED,
                payload={},
            )
        )
