from collections.abc import Awaitable, Callable

from dirty_equals import IsDatetime

from app.adapters.database.tables import OutboxTable
from app.application.exceptions import OutboxPublishException
from app.domain.entities.outbox import (
    Outbox,
    OutboxEventType,
    OutboxStatus,
    PublishNextOutbox,
    PublishOutboxMessage,
)
from app.domain.use_cases.outbox.publish_next import PublishNextOutboxUC
from tests.plugins.use_cases.outbox import FakeOutboxPublisher


async def test__publish_next__none(
    publish_next_outbox_uc: PublishNextOutboxUC,
) -> None:
    assert (
        await publish_next_outbox_uc.execute(
            input_dto=PublishNextOutbox(
                event_type=OutboxEventType.PAYMENT_CREATED,
                max_attempts=3,
            )
        )
        is None
    )


async def test__publish_next(
    publish_next_outbox_uc: PublishNextOutboxUC,
    outbox_publisher: FakeOutboxPublisher,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    db_outbox = await create_outbox(
        event_type=OutboxEventType.PAYMENT_CREATED,
        status=OutboxStatus.PENDING,
        attempts=0,
        last_error=None,
    )
    outbox = await publish_next_outbox_uc.execute(
        input_dto=PublishNextOutbox(
            event_type=OutboxEventType.PAYMENT_CREATED,
            max_attempts=3,
        )
    )
    assert (outbox, outbox_publisher.messages) == (
        Outbox(
            id=db_outbox.id,
            event_type=db_outbox.event_type,
            payload=db_outbox.payload,
            status=OutboxStatus.PUBLISHED,
            attempts=db_outbox.attempts,
            last_error=None,
            published_at=IsDatetime,
            created_at=db_outbox.created_at,
            updated_at=IsDatetime,
        ),
        [
            PublishOutboxMessage(
                id=db_outbox.id,
                event_type=db_outbox.event_type,
                payload=db_outbox.payload,
            )
        ],
    )


async def test__publish_next__retry(
    publish_next_outbox_uc: PublishNextOutboxUC,
    outbox_publisher: FakeOutboxPublisher,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    outbox_publisher.exception = OutboxPublishException("publish failed")
    db_outbox = await create_outbox(
        event_type=OutboxEventType.PAYMENT_CREATED,
        status=OutboxStatus.PENDING,
        attempts=0,
        last_error=None,
    )
    outbox = await publish_next_outbox_uc.execute(
        input_dto=PublishNextOutbox(
            event_type=OutboxEventType.PAYMENT_CREATED,
            max_attempts=3,
        )
    )
    assert outbox == Outbox(
        id=db_outbox.id,
        event_type=db_outbox.event_type,
        payload=db_outbox.payload,
        status=OutboxStatus.PENDING,
        attempts=1,
        last_error="publish failed",
        published_at=db_outbox.published_at,
        created_at=db_outbox.created_at,
        updated_at=IsDatetime,
    )


async def test__publish_next__failed(
    publish_next_outbox_uc: PublishNextOutboxUC,
    outbox_publisher: FakeOutboxPublisher,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    outbox_publisher.exception = OutboxPublishException("publish failed")
    db_outbox = await create_outbox(
        event_type=OutboxEventType.PAYMENT_CREATED,
        status=OutboxStatus.PENDING,
        attempts=2,
        last_error=None,
    )
    outbox = await publish_next_outbox_uc.execute(
        input_dto=PublishNextOutbox(
            event_type=OutboxEventType.PAYMENT_CREATED,
            max_attempts=3,
        )
    )
    assert outbox == Outbox(
        id=db_outbox.id,
        event_type=db_outbox.event_type,
        payload=db_outbox.payload,
        status=OutboxStatus.FAILED,
        attempts=3,
        last_error="publish failed",
        published_at=db_outbox.published_at,
        created_at=db_outbox.created_at,
        updated_at=IsDatetime,
    )
