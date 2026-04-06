import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.storages.payment import PaymentStorage
from app.domain.interfaces.storages.payment import IPaymentStorage


@pytest.fixture
def payment_storage(session: AsyncSession) -> IPaymentStorage:
    return PaymentStorage(session=session)
