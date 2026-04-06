from uuid import UUID

from app.application.exceptions import EntityNotFoundException
from app.application.use_case import IUseCase
from app.domain.entities.movie import Movie
from app.domain.interfaces.storages.movie import IMovieStorage
from app.domain.uow import AbstractUow


class DeleteMovieByIdUC(IUseCase[UUID, None]):
    _movie_storage: IMovieStorage
    _uow: AbstractUow

    def __init__(
        self,
        uow: AbstractUow,
        movie_storage: IMovieStorage,
    ) -> None:
        self._movie_storage = movie_storage
        self._uow = uow

    async def execute(self, *, input_dto: UUID) -> None:
        async with self._uow:
            if not await self._movie_storage.exists_by_id(input_dto=input_dto):
                raise EntityNotFoundException(entity=Movie, entity_id=input_dto)
            await self._movie_storage.delete_by_id(input_dto=input_dto)
