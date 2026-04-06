from app.application.use_case import IUseCase
from app.domain.entities.movie import Movie, UpdateMovie
from app.domain.interfaces.storages.movie import IMovieStorage
from app.domain.uow import AbstractUow


class UpdateMovieByIdUC(IUseCase[UpdateMovie, Movie]):
    _movie_storage: IMovieStorage
    _uow: AbstractUow

    def __init__(
        self,
        uow: AbstractUow,
        movie_storage: IMovieStorage,
    ) -> None:
        self._movie_storage = movie_storage
        self._uow = uow

    async def execute(self, *, input_dto: UpdateMovie) -> Movie:
        async with self._uow:
            return await self._movie_storage.update_by_id(input_dto=input_dto)
