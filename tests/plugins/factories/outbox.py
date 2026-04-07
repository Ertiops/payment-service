from collections.abc import Awaitable, Callable

import pytest
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import OutboxTable
from app.domain.entities.outbox import OutboxEventType, OutboxStatus
from tests.plugins.factories.utils.mixins import TimestampedFactoryMixin


class OutboxTableFactory(SQLAlchemyFactory[OutboxTable], TimestampedFactoryMixin):
    @classmethod
    def event_type(cls) -> OutboxEventType:
        return OutboxEventType.PAYMENT_CREATED

    @classmethod
    def payload(cls) -> dict[str, str]:
        return {"payment_id": "payment-id"}

    @classmethod
    def status(cls) -> OutboxStatus:
        return OutboxStatus.PENDING

    @classmethod
    def attempts(cls) -> int:
        return 0

    @classmethod
    def last_error(cls) -> None:
        return None

    @classmethod
    def published_at(cls) -> None:
        return None


@pytest.fixture
def create_outbox(session: AsyncSession) -> Callable[..., Awaitable[OutboxTable]]:
    async def _factory(**kwargs: object) -> OutboxTable:
        outbox: OutboxTable = OutboxTableFactory.build(**kwargs)
        session.add(outbox)
        await session.flush()
        return outbox

    return _factory
