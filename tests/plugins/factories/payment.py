from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import UUID

import pytest
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import PaymentTable
from tests.plugins.factories.utils.mixins import TimestampedFactoryMixin


class PaymentTableFactory(SQLAlchemyFactory[PaymentTable], TimestampedFactoryMixin):
    processing_status = "ready"
    processing_attempts = 0
    notification_status = "not_sent"
    webhook_attempts = 0
    delivered_at: datetime | None = None
    last_error: str | None = None
    claim_token: UUID | None = None
    lease_until: datetime | None = None


@pytest.fixture
def create_payment(session: AsyncSession) -> Callable[..., Awaitable[PaymentTable]]:
    async def _factory(**kwargs: object) -> PaymentTable:
        payment: PaymentTable = PaymentTableFactory.build(**kwargs)
        session.add(payment)
        await session.flush()
        return payment

    return _factory
