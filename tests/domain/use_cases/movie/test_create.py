from dirty_equals import IsDatetime, IsUUID

from app.domain.entities.movie import (
    CreateMovie,
    Movie,
    MovieGenre,
)
from app.domain.use_cases.movie.create import CreateMovieUC
from tests.utils.common import now_utc


async def test__create(create_movie_uc: CreateMovieUC) -> None:
    create_data = CreateMovie(
        title="test_title",
        description="test_description",
        year=now_utc().year,
        director="test_director",
        genre=MovieGenre.COMEDY,
        duration_minutes=120,
        rating=4.5,
    )
    movie = await create_movie_uc.execute(input_dto=create_data)
    assert movie == Movie(
        id=IsUUID,
        title=create_data.title,
        description=create_data.description,
        year=create_data.year,
        director=create_data.director,
        genre=create_data.genre,
        duration_minutes=create_data.duration_minutes,
        rating=create_data.rating,
        created_at=IsDatetime,
        updated_at=IsDatetime,
    )
