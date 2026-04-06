from app.adapters.database.tables import OutboxTable
from app.domain.entities.outbox import Outbox


def convert_outbox_table_to_dto(
    *,
    result: OutboxTable,
) -> Outbox:
    return Outbox(
        id=result.id,
        event_type=result.event_type,
        payload=result.payload,
        status=result.status,
        attempts=result.attempts,
        last_error=result.last_error,
        published_at=result.published_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
