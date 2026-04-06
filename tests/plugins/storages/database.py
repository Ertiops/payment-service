import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.storages.movie import MovieStorage
from app.adapters.database.storages.user import UserStorage
from app.domain.interfaces.storages.movie import IMovieStorage
from app.domain.interfaces.storages.user import IUserStorage


@pytest.fixture
def movie_storage(session: AsyncSession) -> IMovieStorage:
    return MovieStorage(session=session)


@pytest.fixture
def user_storage(session: AsyncSession) -> IUserStorage:
    return UserStorage(session=session)
