import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.storages.outbox import OutboxStorage
from app.adapters.database.storages.payment import PaymentStorage


@pytest.fixture
def payment_storage(session: AsyncSession) -> PaymentStorage:
    return PaymentStorage(session=session)


@pytest.fixture
def outbox_storage(session: AsyncSession) -> OutboxStorage:
    return OutboxStorage(session=session)
