from collections.abc import Awaitable, Callable

import pytest
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import PaymentTable
from tests.plugins.factories.utils.mixins import TimestampedFactoryMixin


class PaymentTableFactory(SQLAlchemyFactory[PaymentTable], TimestampedFactoryMixin):
    pass


@pytest.fixture
def create_payment(session: AsyncSession) -> Callable[..., Awaitable[PaymentTable]]:
    async def _factory(**kwargs) -> PaymentTable:
        payment: PaymentTable = PaymentTableFactory.build(**kwargs)
        session.add(payment)
        await session.flush()
        return payment

    return _factory
