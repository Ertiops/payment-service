from dirty_equals import IsDatetime, IsUUID

from app.adapters.database.storages.outbox import OutboxStorage
from app.domain.entities.outbox import (
    CreateOutbox,
    Outbox,
    OutboxEventType,
    OutboxStatus,
)


async def test__create(
    outbox_storage: OutboxStorage,
) -> None:
    create_data = CreateOutbox(
        event_type=OutboxEventType.PAYMENT_CREATED,
        payload={"payment_id": "payment-id"},
        status=OutboxStatus.PENDING,
        attempts=0,
        last_error=None,
        published_at=None,
    )
    outbox = await outbox_storage.create(input_dto=create_data)
    assert outbox == Outbox(
        id=IsUUID,
        event_type=create_data.event_type,
        payload=create_data.payload,
        status=create_data.status,
        attempts=create_data.attempts,
        last_error=create_data.last_error,
        published_at=create_data.published_at,
        created_at=IsDatetime,
        updated_at=IsDatetime,
    )
