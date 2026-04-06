from collections.abc import Awaitable, Callable, Mapping
from http import HTTPStatus
from typing import Any

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from app.adapters.database.tables import MovieTable
from app.domain.entities.movie import MovieGenre
from tests.utils.common import now_utc

API_URL = "/api/v1/movies/"


@pytest.mark.parametrize(
    "body",
    (
        dict(title="t" * 2),
        dict(title="t" * 256),
        dict(year=0),
        dict(year=now_utc().year + 1),
        dict(director="t" * 2),
        dict(director="t" * 256),
        dict(genre="test_wrong_genre"),
        dict(duration_minutes=0),
        dict(rating=0),
        dict(rating=11),
    ),
)
async def test__create__unprocessable_entity(
    client: AsyncClient,
    body: Mapping[str, Any],
) -> None:
    response = await client.post(API_URL, json=body)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test__create__ok__status(client: AsyncClient) -> None:
    response = await client.post(
        API_URL,
        json=dict(
            title="test_movie",
            description="test_description",
            year=now_utc().year,
            director="test_director",
            genre=MovieGenre.COMEDY,
            duration_minutes=100,
            rating=4.5,
        ),
    )
    assert response.status_code == HTTPStatus.CREATED


async def test__create__ok__format(client: AsyncClient) -> None:
    body = dict(
        title="test_movie",
        description="test_description",
        year=now_utc().year,
        director="test_director",
        genre=MovieGenre.COMEDY,
        duration_minutes=100,
        rating=4.5,
    )
    response = await client.post(API_URL, json=body)
    assert response.json() == dict(
        id=IsStr,
        title=body.get("title"),
        description=body.get("description"),
        year=body.get("year"),
        director=body.get("director"),
        genre=body.get("genre"),
        duration_minutes=body.get("duration_minutes"),
        rating=body.get("rating"),
        created_at=IsStr,
        updated_at=IsStr,
    )


async def test__create__duplicate__conflict(
    client: AsyncClient,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movie = await create_movie(year=now_utc().year)
    response = await client.post(
        API_URL,
        json=dict(
            title=db_movie.title,
            description="test_description",
            year=db_movie.year,
            director=db_movie.director,
            genre=MovieGenre.COMEDY,
            duration_minutes=120,
            rating=4.5,
        ),
    )
    assert response.status_code == HTTPStatus.CONFLICT
