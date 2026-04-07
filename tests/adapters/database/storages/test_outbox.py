from collections.abc import Awaitable, Callable

import pytest
from dirty_equals import IsDatetime, IsUUID
from uuid6 import uuid7

from app.adapters.database.storages.outbox import OutboxStorage
from app.adapters.database.tables import OutboxTable
from app.application.exceptions import EntityNotFoundException
from app.domain.entities.outbox import (
    CreateOutbox,
    GetOutboxToPublish,
    MarkOutboxAsFailed,
    MarkOutboxAsPublished,
    Outbox,
    OutboxEventType,
    OutboxStatus,
)
from tests.utils.common import now_utc


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


async def test__get_to_publish(
    outbox_storage: OutboxStorage,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    db_outbox = await create_outbox(
        event_type=OutboxEventType.PAYMENT_CREATED,
        status=OutboxStatus.PENDING,
        attempts=0,
    )
    outbox = await outbox_storage.get_to_publish(
        input_dto=GetOutboxToPublish(
            event_type=OutboxEventType.PAYMENT_CREATED,
            status=OutboxStatus.PENDING,
            max_attempts=3,
        )
    )
    assert outbox == Outbox(
        id=db_outbox.id,
        event_type=db_outbox.event_type,
        payload=db_outbox.payload,
        status=db_outbox.status,
        attempts=db_outbox.attempts,
        last_error=db_outbox.last_error,
        published_at=db_outbox.published_at,
        created_at=db_outbox.created_at,
        updated_at=db_outbox.updated_at,
    )


async def test__get_to_publish__none(
    outbox_storage: OutboxStorage,
) -> None:
    assert (
        await outbox_storage.get_to_publish(
            input_dto=GetOutboxToPublish(
                event_type=OutboxEventType.PAYMENT_CREATED,
                status=OutboxStatus.PENDING,
                max_attempts=3,
            )
        )
        is None
    )


async def test__mark_as_published(
    outbox_storage: OutboxStorage,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    db_outbox = await create_outbox(
        status=OutboxStatus.PENDING,
        attempts=1,
        last_error="publish failed",
        published_at=None,
    )
    update_data = MarkOutboxAsPublished(
        id=db_outbox.id,
        status=OutboxStatus.PUBLISHED,
        published_at=now_utc(),
        last_error=None,
    )
    outbox = await outbox_storage.mark_as_published(input_dto=update_data)
    assert outbox == Outbox(
        id=db_outbox.id,
        event_type=db_outbox.event_type,
        payload=db_outbox.payload,
        status=update_data.status,
        attempts=db_outbox.attempts,
        last_error=update_data.last_error,
        published_at=update_data.published_at,
        created_at=db_outbox.created_at,
        updated_at=IsDatetime,
    )


async def test__mark_as_published__entity_not_found_exception(
    outbox_storage: OutboxStorage,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await outbox_storage.mark_as_published(
            input_dto=MarkOutboxAsPublished(
                id=uuid7(),
                status=OutboxStatus.PUBLISHED,
                published_at=now_utc(),
                last_error=None,
            )
        )


async def test__mark_as_failed(
    outbox_storage: OutboxStorage,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    db_outbox = await create_outbox(
        status=OutboxStatus.PENDING,
        attempts=1,
        last_error=None,
        published_at=None,
    )
    update_data = MarkOutboxAsFailed(
        id=db_outbox.id,
        status=OutboxStatus.FAILED,
        attempts=2,
        last_error="publish failed",
    )
    outbox = await outbox_storage.mark_as_failed(input_dto=update_data)
    assert outbox == Outbox(
        id=db_outbox.id,
        event_type=db_outbox.event_type,
        payload=db_outbox.payload,
        status=update_data.status,
        attempts=update_data.attempts,
        last_error=update_data.last_error,
        published_at=db_outbox.published_at,
        created_at=db_outbox.created_at,
        updated_at=IsDatetime,
    )


async def test__mark_as_failed__entity_not_found_exception(
    outbox_storage: OutboxStorage,
) -> None:
    with pytest.raises(EntityNotFoundException):
        await outbox_storage.mark_as_failed(
            input_dto=MarkOutboxAsFailed(
                id=uuid7(),
                status=OutboxStatus.FAILED,
                attempts=1,
                last_error="publish failed",
            )
        )
