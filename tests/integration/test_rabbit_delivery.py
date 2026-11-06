import asyncio
import json
import time

import pytest
from aio_pika import connect_robust
from faststream.rabbit import RabbitBroker
from faststream.rabbit.schemas.channel import Channel
from uuid6 import uuid7

from app.adapters.rabbitmq.config import RabbitMQConfig
from app.adapters.rabbitmq.publishers.outbox import RabbitMQOutboxPublisher
from app.adapters.rabbitmq.topology import declare_payment_topology
from app.domain.entities.outbox import OutboxEventType, PublishOutboxMessage
from tests.utils.rabbit import isolated_rabbit


@pytest.mark.parametrize(
    "event_type,minimum_delay,number",
    [
        (OutboxEventType.PAYMENT_RETRY_1, 0.9, 2),
        (OutboxEventType.PAYMENT_RETRY_2, 1.9, 3),
    ],
)
async def test_real_quorum_ttl_routes_persistent_envelope_after_delay(
    event_type: OutboxEventType,
    minimum_delay: float,
    number: int,
) -> None:
    async with isolated_rabbit() as rabbit:
        config = RabbitMQConfig(dsn=rabbit.dsn)
        broker = RabbitBroker(
            rabbit.dsn,
            default_channel=Channel(publisher_confirms=True, on_return_raises=True),
        )
        await broker.start()
        try:
            await declare_payment_topology(broker, config)
            publisher = RabbitMQOutboxPublisher(broker=broker, config=config)
            async with await connect_robust(rabbit.dsn) as connection:
                channel = await connection.channel()
                queue = await channel.get_queue("payments.new")
                dto = PublishOutboxMessage(
                    id=uuid7(),
                    event_type=event_type,
                    payload={"payment_id": str(uuid7()), "attempt": number},
                )
                async with queue.iterator() as messages:
                    started = time.monotonic()
                    await publisher.publish(input_dto=dto)
                    async with asyncio.timeout(8):
                        message = await anext(messages)
                    elapsed = time.monotonic() - started
                    payload = json.loads(message.body)
                    message_id = message.message_id
                    await message.ack()
        finally:
            await broker.stop()
    assert (payload, message_id, elapsed >= minimum_delay) == (
        dict(dto.payload),
        str(dto.id),
        True,
    )
