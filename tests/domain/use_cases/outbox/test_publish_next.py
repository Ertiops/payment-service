from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import OutboxTable
from app.application.exceptions import OutboxPublishException
from app.domain.entities.outbox import PublishNextOutbox
from app.domain.use_cases.outbox.publish_next import PublishNextOutboxUC
from tests.plugins.use_cases.outbox import FakeOutboxPublisher

POLL = PublishNextOutbox(initial_delay_seconds=1, max_delay_seconds=30)


async def test_no_pending_event(publish_next_outbox_uc: PublishNextOutboxUC) -> None:
    assert await publish_next_outbox_uc.execute(input_dto=POLL) is None


async def test_publish_preserves_event_id_and_payload(
    publish_next_outbox_uc: PublishNextOutboxUC,
    outbox_publisher: FakeOutboxPublisher,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    row = await create_outbox()
    result = await publish_next_outbox_uc.execute(input_dto=POLL)
    assert (result.status, [(m.id, m.payload) for m in outbox_publisher.messages]) == (
        "published",
        [(row.id, row.payload)],
    )


async def test_broker_outage_does_not_exhaust_consumer_budget(
    publish_next_outbox_uc: PublishNextOutboxUC,
    outbox_publisher: FakeOutboxPublisher,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    outbox_publisher.exception = OutboxPublishException("offline")
    await create_outbox(attempts=100)
    result = await publish_next_outbox_uc.execute(input_dto=POLL)
    assert (result.status, result.attempts, result.last_error) == (
        "pending",
        101,
        "offline",
    )


async def test_publication_waits_until_transport_backoff_expires(
    publish_next_outbox_uc: PublishNextOutboxUC,
    outbox_publisher: FakeOutboxPublisher,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
) -> None:
    outbox_publisher.exception = OutboxPublishException("offline")
    await create_outbox()
    await publish_next_outbox_uc.execute(input_dto=POLL)
    outbox_publisher.exception = None
    assert await publish_next_outbox_uc.execute(input_dto=POLL) is None


async def test_publication_retry_backoff_is_capped(
    publish_next_outbox_uc: PublishNextOutboxUC,
    outbox_publisher: FakeOutboxPublisher,
    create_outbox: Callable[..., Awaitable[OutboxTable]],
    session: AsyncSession,
) -> None:
    outbox_publisher.exception = OutboxPublishException("offline")
    row = await create_outbox(attempts=100)
    await publish_next_outbox_uc.execute(input_dto=POLL)
    stored = await session.scalar(select(OutboxTable).where(OutboxTable.id == row.id))
    assert 29 <= (stored.available_at - stored.updated_at).total_seconds() <= 31
