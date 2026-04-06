from uuid import UUID

from app.application.exceptions import EntityNotFoundException
from app.application.use_case import IUseCase
from app.domain.entities.movie import Movie
from app.domain.interfaces.storages.movie import IMovieStorage
from app.domain.uow import AbstractUow


class GetMovieByIdUC(IUseCase[UUID, Movie]):
    _movie_storage: IMovieStorage
    _uow: AbstractUow

    def __init__(
        self,
        uow: AbstractUow,
        movie_storage: IMovieStorage,
    ) -> None:
        self._movie_storage = movie_storage
        self._uow = uow

    async def execute(self, *, input_dto: UUID) -> Movie:
        async with self._uow:
            movie = await self._movie_storage.get_by_id(input_dto=input_dto)
            if movie is None:
                raise EntityNotFoundException(entity=Movie, entity_id=input_dto)
            return movie
