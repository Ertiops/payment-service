from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from uuid import UUID

from app.application.entities import UNSET, Unset
from app.domain.entities.common import Pagination, ToDictMixin


@unique
class MovieGenre(StrEnum):
    ACTION = "action"
    ADVENTURE = "adventure"
    ANIMATION = "animation"
    COMEDY = "comedy"
    CRIME = "crime"
    DOCUMENTARY = "documentary"
    DRAMA = "drama"
    FANTASY = "fantasy"
    HISTORICAL = "historical"
    HORROR = "horror"
    MUSICAL = "musical"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    THRILLER = "thriller"
    WAR = "war"
    WESTERN = "western"
    BIOGRAPHY = "biography"
    FAMILY = "family"
    SPORT = "sport"
    SUPERHERO = "superhero"
    NOIR = "noir"


@dataclass(frozen=True, kw_only=True, slots=True)
class Movie:
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


@dataclass(frozen=True, kw_only=True, slots=True)
class MovieListParams(Pagination): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateMovie(ToDictMixin):
    title: str
    description: str
    year: int
    director: str
    genre: str
    duration_minutes: int
    rating: float


@dataclass(frozen=True, kw_only=True, slots=True)
class UpdateMovie(ToDictMixin):
    id: UUID
    title: str | Unset = UNSET
    description: str | Unset = UNSET
    year: int | Unset = UNSET
    director: str | Unset = UNSET
    genre: MovieGenre | Unset = UNSET
    duration_minutes: int | Unset = UNSET
    rating: float | Unset = UNSET
