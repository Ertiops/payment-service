from collections.abc import Awaitable, Callable, Mapping
from http import HTTPStatus
from typing import Any
from uuid import UUID

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import MovieTable

API_URL = "/api/v1/movies/"


@pytest.mark.parametrize(
    "params",
    [
        dict(limit=-1),
        dict(limit=0),
        dict(limit="a"),
        dict(offset=-1),
        dict(offset="a"),
        dict(limit=101),
    ],
)
async def test__get_list__unprocessable_entity(
    client: AsyncClient, params: Mapping[str, Any]
) -> None:
    response = await client.get(API_URL, params=params)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__get_list__ok__status(client: AsyncClient) -> None:
    response = await client.get(API_URL)
    assert response.status_code == HTTPStatus.OK


async def test__get_list__ok__format(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    response = await client.get(API_URL)
    assert response.json() == dict(
        total=len(db_movies),
        items=[
            dict(
                id=str(db_movie.id),
                title=db_movie.title,
                description=db_movie.description,
                year=db_movie.year,
                director=db_movie.director,
                genre=db_movie.genre,
                duration_minutes=db_movie.duration_minutes,
                rating=db_movie.rating,
                created_at=IsStr,
                updated_at=IsStr,
            )
            for db_movie in db_movies
        ],
    )


async def test__get_list__validate_limit(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    response = await client.get(API_URL, params=dict(limit=1))
    assert response.json() == dict(
        total=len(db_movies),
        items=[
            dict(
                id=str(db_movie.id),
                title=db_movie.title,
                description=db_movie.description,
                year=db_movie.year,
                director=db_movie.director,
                genre=db_movie.genre,
                duration_minutes=db_movie.duration_minutes,
                rating=db_movie.rating,
                created_at=IsStr,
                updated_at=IsStr,
            )
            for db_movie in db_movies
        ][:1],
    )


async def test__get_list__validate_offset(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    response = await client.get(API_URL, params=dict(offset=1))
    assert response.json() == dict(
        total=len(db_movies),
        items=[
            dict(
                id=str(db_movie.id),
                title=db_movie.title,
                description=db_movie.description,
                year=db_movie.year,
                director=db_movie.director,
                genre=db_movie.genre,
                duration_minutes=db_movie.duration_minutes,
                rating=db_movie.rating,
                created_at=IsStr,
                updated_at=IsStr,
            )
            for db_movie in db_movies
        ][1:],
    )


async def test__get_list__empty_list(client: AsyncClient) -> None:
    response = await client.get(API_URL)
    assert response.json() == dict(
        total=0,
        items=[],
    )
