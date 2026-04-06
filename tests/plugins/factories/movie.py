from collections.abc import Awaitable, Callable

import pytest
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.tables import MovieTable
from tests.plugins.factories.utils.mixins import TimestampedFactoryMixin


class MovieTableFactory(SQLAlchemyFactory[MovieTable], TimestampedFactoryMixin):
    pass


@pytest.fixture
def create_movie(session: AsyncSession) -> Callable[..., Awaitable[MovieTable]]:
    async def _factory(**kwargs) -> MovieTable:
        movie: MovieTable = MovieTableFactory.build(**kwargs)
        session.add(movie)
        await session.flush()
        return movie

    return _factory
