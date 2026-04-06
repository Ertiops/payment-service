from collections.abc import Awaitable, Callable
from uuid import UUID

from app.adapters.database.tables import MovieTable
from app.domain.entities.common import ItemList
from app.domain.entities.movie import (
    Movie,
    MovieListParams,
)
from app.domain.use_cases.movie.get_list import GetMovieListUC


async def test__get_list(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    movies = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=10, offset=0)
    )
    assert movies == ItemList(
        total=len(db_movies),
        items=[
            Movie(
                id=db_movie.id,
                title=db_movie.title,
                description=db_movie.description,
                year=db_movie.year,
                director=db_movie.director,
                genre=db_movie.genre,
                duration_minutes=db_movie.duration_minutes,
                rating=db_movie.rating,
                created_at=db_movie.created_at,
                updated_at=db_movie.updated_at,
            )
            for db_movie in db_movies
        ],
    )


async def test__get_list__validate_limit(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    movies = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=1, offset=0)
    )
    assert movies == ItemList(
        total=len(db_movies),
        items=[
            Movie(
                id=db_movie.id,
                title=db_movie.title,
                description=db_movie.description,
                year=db_movie.year,
                director=db_movie.director,
                genre=db_movie.genre,
                duration_minutes=db_movie.duration_minutes,
                rating=db_movie.rating,
                created_at=db_movie.created_at,
                updated_at=db_movie.updated_at,
            )
            for db_movie in db_movies
        ][:1],
    )


async def test__get_list__validate_offset(
    get_movie_list_uc: GetMovieListUC,
    create_movie: Callable[..., Awaitable[MovieTable]],
) -> None:
    db_movies = [await create_movie(id=UUID(int=i + 1)) for i in range(2)]
    movies = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=2, offset=1)
    )
    assert movies == ItemList(
        total=len(db_movies),
        items=[
            Movie(
                id=db_movie.id,
                title=db_movie.title,
                description=db_movie.description,
                year=db_movie.year,
                director=db_movie.director,
                genre=db_movie.genre,
                duration_minutes=db_movie.duration_minutes,
                rating=db_movie.rating,
                created_at=db_movie.created_at,
                updated_at=db_movie.updated_at,
            )
            for db_movie in db_movies
        ][1:],
    )


async def test__get_list__empty_list(get_movie_list_uc: GetMovieListUC) -> None:
    movies = await get_movie_list_uc.execute(
        input_dto=MovieListParams(limit=2, offset=1)
    )
    assert movies == ItemList(total=0, items=[])
