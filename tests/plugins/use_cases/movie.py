import pytest

from app.domain.interfaces.storages.movie import IMovieStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.movie.create import CreateMovieUC
from app.domain.use_cases.movie.delete_by_id import DeleteMovieByIdUC
from app.domain.use_cases.movie.get_by_id import GetMovieByIdUC
from app.domain.use_cases.movie.get_list import GetMovieListUC
from app.domain.use_cases.movie.update_by_id import UpdateMovieByIdUC


@pytest.fixture
def create_movie_uc(uow: AbstractUow, movie_storage: IMovieStorage) -> CreateMovieUC:
    return CreateMovieUC(
        uow=uow,
        movie_storage=movie_storage,
    )


@pytest.fixture
def get_movie_by_id_uc(
    uow: AbstractUow, movie_storage: IMovieStorage
) -> GetMovieByIdUC:
    return GetMovieByIdUC(
        uow=uow,
        movie_storage=movie_storage,
    )


@pytest.fixture
def get_movie_list_uc(uow: AbstractUow, movie_storage: IMovieStorage) -> GetMovieListUC:
    return GetMovieListUC(
        uow=uow,
        movie_storage=movie_storage,
    )


@pytest.fixture
def update_movie_by_id_uc(
    uow: AbstractUow, movie_storage: IMovieStorage
) -> UpdateMovieByIdUC:
    return UpdateMovieByIdUC(
        uow=uow,
        movie_storage=movie_storage,
    )


@pytest.fixture
def delete_movie_by_id_uc(
    uow: AbstractUow, movie_storage: IMovieStorage
) -> DeleteMovieByIdUC:
    return DeleteMovieByIdUC(
        uow=uow,
        movie_storage=movie_storage,
    )
