from typing import Protocol

from app.domain.entities.outbox import CreateOutbox, Outbox


class IOutboxStorage(Protocol):
    async def create(self, *, input_dto: CreateOutbox) -> Outbox:
        pass
