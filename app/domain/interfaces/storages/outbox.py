from typing import Protocol

from app.domain.entities.outbox import (
    CreateOutbox,
    GetOutboxToPublish,
    MarkOutboxAsFailed,
    MarkOutboxAsPublished,
    Outbox,
)


class IOutboxStorage(Protocol):
    async def create(self, *, input_dto: CreateOutbox) -> Outbox:
        pass

    async def get_to_publish(self, *, input_dto: GetOutboxToPublish) -> Outbox | None:
        pass

    async def mark_as_published(self, *, input_dto: MarkOutboxAsPublished) -> Outbox:
        pass

    async def mark_as_failed(self, *, input_dto: MarkOutboxAsFailed) -> Outbox:
        pass
