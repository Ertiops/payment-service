from app.adapters.database.tables import MovieTable
from app.domain.entities.movie import Movie


def convert_movie_table_to_dto(
    *,
    result: MovieTable,
) -> Movie:
    return Movie(
        id=result.id,
        title=result.title,
        description=result.description,
        year=result.year,
        director=result.director,
        genre=result.genre,
        duration_minutes=result.duration_minutes,
        rating=result.rating,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
