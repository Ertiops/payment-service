from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.converters.outbox import convert_outbox_table_to_dto
from app.adapters.database.tables import OutboxTable
from app.domain.entities.outbox import CreateOutbox, Outbox
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
                status=input_dto.status,
                attempts=input_dto.attempts,
                last_error=input_dto.last_error,
                published_at=input_dto.published_at,
            )
            .returning(OutboxTable)
        )
        result = (await self.session.scalars(stmt)).one()
        return convert_outbox_table_to_dto(result=result)
