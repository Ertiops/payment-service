from collections.abc import Awaitable, Callable

from app.adapters.database.tables import UserTable
from app.domain.entities.common import ItemList
from app.domain.entities.user import (
    User,
    UserListParams,
)
from app.domain.use_cases.user.get_list import GetUserListUC


async def test__get_list(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user() for _ in range(2)]
    users = await get_user_list_uc.execute(input_dto=UserListParams(limit=10, offset=0))
    assert users == ItemList(
        total=len(db_users),
        items=[
            User(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
            for db_user in db_users
        ],
    )


async def test__get_list__validate_limit(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user() for _ in range(2)]
    users = await get_user_list_uc.execute(input_dto=UserListParams(limit=1, offset=0))
    assert users == ItemList(
        total=len(db_users),
        items=[
            User(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
            for db_user in db_users
        ][0:1],
    )


async def test__get_list__validate_offset(
    get_user_list_uc: GetUserListUC,
    create_user: Callable[..., Awaitable[UserTable]],
) -> None:
    db_users = [await create_user() for _ in range(2)]
    users = await get_user_list_uc.execute(input_dto=UserListParams(limit=1, offset=1))
    assert users == ItemList(
        total=len(db_users),
        items=[
            User(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
            for db_user in db_users
        ][1:],
    )


async def test__get_list__empty_list(
    get_user_list_uc: GetUserListUC,
) -> None:
    users = await get_user_list_uc.execute(input_dto=UserListParams(limit=10, offset=0))
    assert users == ItemList(total=0, items=[])
