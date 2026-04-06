from collections.abc import Awaitable, Callable

import pytest
from dirty_equals import IsDatetime, IsUUID

from app.adapters.database.tables import UserTable
from app.application.exceptions import EntityAlreadyExistsException
from app.domain.entities.user import CreateUser, User
from app.domain.use_cases.user.create import CreateUserUC


async def test__create(
    create_user_uc: CreateUserUC,
) -> None:
    input_dto = CreateUser(
        username="test_username",
        email="test@test.com",
    )
    user = await create_user_uc.execute(input_dto=input_dto)
    assert user == User(
        id=IsUUID,
        username=input_dto.username,
        email=input_dto.email,
        created_at=IsDatetime,
        updated_at=IsDatetime,
    )


async def test__create__entity_already_exists_exception__username(
    create_user_uc: CreateUserUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    with pytest.raises(EntityAlreadyExistsException):
        await create_user_uc.execute(
            input_dto=CreateUser(
                username=db_user.username,
                email="test@test.com",
            )
        )


async def test__create__entity_already_exists_exception__email(
    create_user_uc: CreateUserUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_user = await create_user()
    with pytest.raises(EntityAlreadyExistsException):
        await create_user_uc.execute(
            input_dto=CreateUser(
                username="test_username",
                email=db_user.email,
            )
        )
