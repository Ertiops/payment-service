from collections.abc import Mapping

from faststream.rabbit import RabbitBroker, RabbitQueue
from faststream.rabbit.schemas.queue import QueueType, QuorumQueueArgs

from app.adapters.rabbitmq.config import RabbitMQConfig
from app.domain.entities.outbox import OutboxEventType

PAYMENTS_NEW_QUEUE_NAME = OutboxEventType.PAYMENT_CREATED.value
PAYMENTS_NEW_DLQ_NAME = OutboxEventType.PAYMENT_DEAD_LETTER.value


def payment_queues(delay_seconds: float) -> Mapping[OutboxEventType, RabbitQueue]:
    safe_dlx: QuorumQueueArgs = {
        "x-dead-letter-exchange": "",
        "x-dead-letter-strategy": "at-least-once",
        "x-overflow": "reject-publish",
    }
    return {
        OutboxEventType.PAYMENT_DEAD_LETTER: RabbitQueue(
            name=PAYMENTS_NEW_DLQ_NAME,
            queue_type=QueueType.QUORUM,
            durable=True,
        ),
        OutboxEventType.PAYMENT_CREATED: RabbitQueue(
            name=PAYMENTS_NEW_QUEUE_NAME,
            queue_type=QueueType.QUORUM,
            durable=True,
            arguments={
                **safe_dlx,
                "x-dead-letter-routing-key": PAYMENTS_NEW_DLQ_NAME,
                "x-single-active-consumer": True,
            },
        ),
        OutboxEventType.PAYMENT_RETRY_1: RabbitQueue(
            name=OutboxEventType.PAYMENT_RETRY_1.value,
            queue_type=QueueType.QUORUM,
            durable=True,
            arguments={
                **safe_dlx,
                "x-message-ttl": round(delay_seconds * 1000),
                "x-dead-letter-routing-key": PAYMENTS_NEW_QUEUE_NAME,
            },
        ),
        OutboxEventType.PAYMENT_RETRY_2: RabbitQueue(
            name=OutboxEventType.PAYMENT_RETRY_2.value,
            queue_type=QueueType.QUORUM,
            durable=True,
            arguments={
                **safe_dlx,
                "x-message-ttl": round(delay_seconds * 2000),
                "x-dead-letter-routing-key": PAYMENTS_NEW_QUEUE_NAME,
            },
        ),
    }


async def declare_payment_topology(
    broker: RabbitBroker, config: RabbitMQConfig
) -> None:
    for queue in payment_queues(config.retry_delay_seconds).values():
        await broker.declare_queue(queue)


PAYMENTS_NEW_QUEUE = payment_queues(1)[OutboxEventType.PAYMENT_CREATED]
PAYMENTS_NEW_DLQ = payment_queues(1)[OutboxEventType.PAYMENT_DEAD_LETTER]
