from collections.abc import Awaitable, Callable

import pytest
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import UserTable
from tests.plugins.factories.utils.iteruse import IterUse
from tests.plugins.factories.utils.mixins import TimestampedFactoryMixin


class UserTableFactory(SQLAlchemyFactory[UserTable], TimestampedFactoryMixin):
    email = IterUse[str](lambda count: f"test{count}@test.com")
    username = IterUse[str](lambda count: f"test_username{count}")


@pytest.fixture
def create_user(session: AsyncSession) -> Callable[..., Awaitable[UserTable]]:
    async def _factory(**kwargs) -> UserTable:
        user: UserTable = UserTableFactory.build(**kwargs)
        session.add(user)
        await session.flush()
        return user

    return _factory
