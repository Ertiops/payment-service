import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.storages.payment import PaymentStorage


@pytest.fixture
def payment_storage(session: AsyncSession) -> PaymentStorage:
    return PaymentStorage(session=session)
