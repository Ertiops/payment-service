from typing import Any

import pytest
from dishka import AnyOf, Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.adapters.database.uow import SqlalchemyUow
from app.domain.uow import AbstractUow
from tests.utils.worker import get_worker_name

TEST_SESSIONS: dict[str, AsyncSession] = {}


class TestDBUOW(AbstractUow):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._sp: AsyncSessionTransaction | None = None

    async def create_transaction(self) -> None:
        self._sp = await self.session.begin_nested()

    async def commit(self) -> None:
        await self.session.flush()
        if self._sp is not None:
            await self._sp.commit()

    async def rollback(self) -> None:
        if self._sp is not None:
            await self._sp.rollback()

    async def close_transaction(self, *exc: Any) -> None:
        self._sp = None


class TestDBProvider(Provider):
    @provide(scope=Scope.REQUEST, override=True)
    async def get_session(self) -> AsyncSession:
        return TEST_SESSIONS[get_worker_name()]

    @provide(scope=Scope.REQUEST, override=True)
    def uow(self, session: AsyncSession) -> AnyOf[SqlalchemyUow, AbstractUow]:
        return TestDBUOW(session=session)


@pytest.fixture(scope="session")
async def test_db_provider() -> TestDBProvider:
    return TestDBProvider()


@pytest.fixture
def uow(session: AsyncSession) -> AbstractUow:
    return TestDBUOW(session=session)
