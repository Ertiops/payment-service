import pytest

from app.domain.interfaces.storages.user import IUserStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.user.create import CreateUserUC
from app.domain.use_cases.user.delete_by_id import DeleteUserByIdUC
from app.domain.use_cases.user.get_by_id import GetUserByIdUC
from app.domain.use_cases.user.get_list import GetUserListUC
from app.domain.use_cases.user.update_by_id import UpdateUserByIdUC


@pytest.fixture
def create_user_uc(uow: AbstractUow, user_storage: IUserStorage) -> CreateUserUC:
    return CreateUserUC(
        uow=uow,
        user_storage=user_storage,
    )


@pytest.fixture
def get_user_by_id_uc(uow: AbstractUow, user_storage: IUserStorage) -> GetUserByIdUC:
    return GetUserByIdUC(
        uow=uow,
        user_storage=user_storage,
    )


@pytest.fixture
def get_user_list_uc(uow: AbstractUow, user_storage: IUserStorage) -> GetUserListUC:
    return GetUserListUC(
        uow=uow,
        user_storage=user_storage,
    )


@pytest.fixture
def update_user_by_id_uc(
    uow: AbstractUow, user_storage: IUserStorage
) -> UpdateUserByIdUC:
    return UpdateUserByIdUC(
        uow=uow,
        user_storage=user_storage,
    )


@pytest.fixture
def delete_user_by_id_uc(
    uow: AbstractUow, user_storage: IUserStorage
) -> DeleteUserByIdUC:
    return DeleteUserByIdUC(
        uow=uow,
        user_storage=user_storage,
    )
