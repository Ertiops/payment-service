from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field, PositiveInt

from app.domain.entities.movie import MovieGenre
from app.presenters.rest.schemas import BaseSchema, ItemListSchema, PaginationSchema


class MovieSchema(BaseSchema):
    id: UUID
    title: str
    description: str
    year: int
    director: str
    genre: MovieGenre
    duration_minutes: int
    rating: float
    created_at: datetime
    updated_at: datetime


class MovieListParamsSchema(PaginationSchema): ...


class MovieListSchema(ItemListSchema[MovieSchema]): ...


class CreateMovieSchema(BaseSchema):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3, max_length=2000)
    year: PositiveInt = Field(ge=0, le=datetime.now(tz=UTC).year)
    director: str = Field(min_length=3, max_length=255)
    genre: MovieGenre
    duration_minutes: int = Field(ge=0)
    rating: float = Field(ge=0, le=10)


class UpdateMovieSchema(BaseSchema):
    title: str | None = Field(min_length=3, max_length=255, default=None)
    description: str | None = Field(min_length=3, max_length=2000, default=None)
    year: int | None = Field(ge=0, le=datetime.now(tz=UTC).year, default=None)
    director: str | None = Field(min_length=3, max_length=255, default=None)
    genre: MovieGenre | None = Field(default=None)
    duration_minutes: int | None = Field(ge=0, default=None)
    rating: float | None = Field(ge=0, le=10, default=None)
