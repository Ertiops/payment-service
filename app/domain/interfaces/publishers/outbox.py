from typing import Protocol

from app.domain.entities.outbox import PublishOutboxMessage


class IOutboxPublisher(Protocol):
    async def publish(self, *, input_dto: PublishOutboxMessage) -> None:
        pass
