from uuid import UUID

from app.application.exceptions import EntityNotFoundException
from app.application.use_case import IUseCase
from app.domain.entities.user import User
from app.domain.interfaces.storages.user import IUserStorage
from app.domain.uow import AbstractUow


class DeleteUserByIdUC(IUseCase[UUID, None]):
    _user_storage: IUserStorage
    _uow: AbstractUow

    def __init__(
        self,
        uow: AbstractUow,
        user_storage: IUserStorage,
    ) -> None:
        self._user_storage = user_storage
        self._uow = uow

    async def execute(self, *, input_dto: UUID) -> None:
        async with self._uow:
            if not await self._user_storage.exists_by_id(input_dto=input_dto):
                raise EntityNotFoundException(entity=User, entity_id=input_dto)
            await self._user_storage.delete_by_id(input_dto=input_dto)
