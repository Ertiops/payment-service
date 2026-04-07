from typing import Final

from faststream.rabbit import RabbitQueue
from faststream.rabbit.schemas.queue import QueueType

PAYMENTS_NEW_QUEUE_NAME: Final[str] = "payments.new"
PAYMENTS_NEW_DLQ_NAME: Final[str] = "payments.new.dlq"
PAYMENTS_NEW_DELIVERY_LIMIT: Final[int] = 3


PAYMENTS_NEW_DLQ = RabbitQueue(
    name=PAYMENTS_NEW_DLQ_NAME,
    queue_type=QueueType.QUORUM,
    durable=True,
)

PAYMENTS_NEW_QUEUE = RabbitQueue(
    name=PAYMENTS_NEW_QUEUE_NAME,
    queue_type=QueueType.QUORUM,
    durable=True,
    arguments={
        "x-delivery-limit": PAYMENTS_NEW_DELIVERY_LIMIT,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": PAYMENTS_NEW_DLQ_NAME,
    },
)
