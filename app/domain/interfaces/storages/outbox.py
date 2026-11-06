from typing import Protocol

from app.domain.entities.outbox import (
    CreateOutbox,
    GetOutboxToPublish,
    MarkOutboxAsPublished,
    Outbox,
    RescheduleOutbox,
)


class IOutboxStorage(Protocol):
    async def reschedule(self, *, input_dto: RescheduleOutbox) -> Outbox: ...

    async def create(self, *, input_dto: CreateOutbox) -> Outbox: ...

    async def get_to_publish(
        self, *, input_dto: GetOutboxToPublish
    ) -> Outbox | None: ...

    async def mark_as_published(
        self, *, input_dto: MarkOutboxAsPublished
    ) -> Outbox: ...
