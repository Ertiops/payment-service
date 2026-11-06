from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.converters.outbox import convert_outbox_table_to_dto
from app.adapters.database.outbox_queries import (
    publication_due_conditions,
    publication_retry_values,
)
from app.adapters.database.tables import OutboxTable
from app.application.exceptions import EntityNotFoundException
from app.domain.entities.outbox import (
    CreateOutbox,
    GetOutboxToPublish,
    MarkOutboxAsPublished,
    Outbox,
    OutboxStatus,
    RescheduleOutbox,
)
from app.domain.interfaces.storages.outbox import IOutboxStorage


class OutboxStorage(IOutboxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, input_dto: CreateOutbox) -> Outbox:
        stmt = (
            insert(OutboxTable)
            .values(
                event_type=input_dto.event_type,
                payload=input_dto.payload,
                status=OutboxStatus.PENDING,
                attempts=0,
                last_error=None,
                published_at=None,
            )
            .returning(OutboxTable)
        )
        result = (await self.session.scalars(stmt)).one()
        return convert_outbox_table_to_dto(result=result)

    async def get_to_publish(self, *, input_dto: GetOutboxToPublish) -> Outbox | None:
        stmt = (
            select(OutboxTable)
            .where(*publication_due_conditions(input_dto))
            .order_by(OutboxTable.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.scalar(stmt)
        return convert_outbox_table_to_dto(result=result) if result else None

    async def reschedule(self, *, input_dto: RescheduleOutbox) -> Outbox:
        stmt = (
            update(OutboxTable)
            .where(OutboxTable.id == input_dto.id, OutboxTable.deleted_at.is_(None))
            .values(**publication_retry_values(input_dto))
            .returning(OutboxTable)
        )
        try:
            result = (await self.session.scalars(stmt)).one()
        except NoResultFound as e:
            raise EntityNotFoundException(entity=Outbox, entity_id=input_dto.id) from e
        return convert_outbox_table_to_dto(result=result)

    async def mark_as_published(self, *, input_dto: MarkOutboxAsPublished) -> Outbox:
        stmt = (
            update(OutboxTable)
            .where(
                OutboxTable.id == input_dto.id,
                OutboxTable.deleted_at.is_(None),
            )
            .values(
                status=OutboxStatus.PUBLISHED,
                published_at=input_dto.published_at,
                last_error=None,
            )
            .returning(OutboxTable)
        )
        try:
            result = (await self.session.scalars(stmt)).one()
        except NoResultFound as e:
            raise EntityNotFoundException(entity=Outbox, entity_id=input_dto.id) from e
        return convert_outbox_table_to_dto(result=result)
