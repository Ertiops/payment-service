from datetime import UTC, datetime

from app.application.exceptions import OutboxPublishException
from app.application.use_case import IUseCase
from app.domain.entities.outbox import (
    GetOutboxToPublish,
    MarkOutboxAsFailed,
    MarkOutboxAsPublished,
    Outbox,
    OutboxStatus,
    PublishNextOutbox,
    PublishOutboxMessage,
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
                    event_type=input_dto.event_type,
                    status=OutboxStatus.PENDING,
                    max_attempts=input_dto.max_attempts,
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
                return await self._outbox_storage.mark_as_failed(
                    input_dto=MarkOutboxAsFailed(
                        id=outbox.id,
                        status=(
                            OutboxStatus.FAILED
                            if attempts >= input_dto.max_attempts
                            else OutboxStatus.PENDING
                        ),
                        attempts=attempts,
                        last_error=str(e),
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
