from collections.abc import Callable, Mapping
from http import HTTPStatus
from typing import Any

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import UserTable

API_URL = "/api/v1/users/"


@pytest.mark.parametrize(
    "params",
    [
        dict(limit=-1),
        dict(offset=-1),
        dict(limit="a"),
        dict(offset="a"),
        dict(limit=101),
    ],
)
async def test__get_list__unprocessable_entity(
    client: AsyncClient,
    params: Mapping[str, Any],
) -> None:
    response = await client.get(API_URL, params=params)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__get_list__ok__status(client: AsyncClient) -> None:
    response = await client.get(API_URL)
    assert response.status_code == HTTPStatus.OK


async def test_get_list__ok__format(
    create_user: Callable,
    client: AsyncClient,
) -> None:
    db_users: list[UserTable] = [await create_user() for _ in range(2)]
    response = await client.get(API_URL)
    assert response.json() == dict(
        total=len(db_users),
        items=[
            dict(
                id=str(db_user.id),
                username=db_user.username,
                email=db_user.email,
                created_at=IsStr,
                updated_at=IsStr,
            )
            for db_user in db_users
        ],
    )


async def test_get_list__validate_limit(
    create_user: Callable,
    client: AsyncClient,
) -> None:
    db_users: list[UserTable] = [await create_user() for _ in range(2)]
    response = await client.get(API_URL, params=dict(limit=1))
    assert response.json() == dict(
        total=len(db_users),
        items=[
            dict(
                id=str(db_user.id),
                username=db_user.username,
                email=db_user.email,
                created_at=IsStr,
                updated_at=IsStr,
            )
            for db_user in db_users
        ][:1],
    )


async def test_get_list__validate_offset(
    create_user: Callable,
    client: AsyncClient,
) -> None:
    db_users: list[UserTable] = [await create_user() for _ in range(2)]
    response = await client.get(API_URL, params=dict(offset=1))
    assert response.json() == dict(
        total=len(db_users),
        items=[
            dict(
                id=str(db_user.id),
                username=db_user.username,
                email=db_user.email,
                created_at=IsStr,
                updated_at=IsStr,
            )
            for db_user in db_users
        ][1:],
    )
