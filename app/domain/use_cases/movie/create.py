from app.application.use_case import IUseCase
from app.domain.entities.movie import CreateMovie, Movie
from app.domain.interfaces.storages.movie import IMovieStorage
from app.domain.uow import AbstractUow


class CreateMovieUC(IUseCase[CreateMovie, Movie]):
    _movie_storage: IMovieStorage
    _uow: AbstractUow

    def __init__(
        self,
        uow: AbstractUow,
        movie_storage: IMovieStorage,
    ) -> None:
        self._movie_storage = movie_storage
        self._uow = uow

    async def execute(self, *, input_dto: CreateMovie) -> Movie:
        async with self._uow:
            return await self._movie_storage.create(input_dto=input_dto)
