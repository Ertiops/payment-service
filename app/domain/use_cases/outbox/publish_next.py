from datetime import UTC, datetime, timedelta

from app.application.exceptions import OutboxPublishException
from app.application.use_case import IUseCase
from app.domain.entities.outbox import (
    GetOutboxToPublish,
    MarkOutboxAsPublished,
    Outbox,
    OutboxStatus,
    PublishNextOutbox,
    PublishOutboxMessage,
    RescheduleOutbox,
)
from app.domain.interfaces.publishers.outbox import IOutboxPublisher
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.uow import AbstractUow


class PublishNextOutboxUC(IUseCase[PublishNextOutbox, Outbox | None]):
    def __init__(
        self,
        uow: AbstractUow,
        outbox_storage: IOutboxStorage,
        outbox_publisher: IOutboxPublisher,
    ) -> None:
        self._uow = uow
        self._outbox_storage = outbox_storage
        self._outbox_publisher = outbox_publisher

    async def execute(self, *, input_dto: PublishNextOutbox) -> Outbox | None:
        async with self._uow:
            outbox = await self._outbox_storage.get_to_publish(
                input_dto=GetOutboxToPublish(
                    now=datetime.now(tz=UTC),
                )
            )
            if outbox is None:
                return None

            try:
                await self._outbox_publisher.publish(
                    input_dto=PublishOutboxMessage(
                        id=outbox.id,
                        event_type=outbox.event_type,
                        payload=outbox.payload,
                    )
                )
            except OutboxPublishException as e:
                attempts = outbox.attempts + 1
                delay = min(
                    input_dto.initial_delay_seconds * 2 ** min(attempts - 1, 30),
                    input_dto.max_delay_seconds,
                )
                return await self._outbox_storage.reschedule(
                    input_dto=RescheduleOutbox(
                        id=outbox.id,
                        attempts=attempts,
                        last_error=str(e)[:2000],
                        available_at=datetime.now(tz=UTC) + timedelta(seconds=delay),
                    )
                )

            return await self._outbox_storage.mark_as_published(
                input_dto=MarkOutboxAsPublished(
                    id=outbox.id,
                    status=OutboxStatus.PUBLISHED,
                    published_at=datetime.now(tz=UTC),
                    last_error=None,
                )
            )
