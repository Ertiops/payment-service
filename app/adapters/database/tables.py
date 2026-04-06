from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.database.base import BaseTable, IdentifableMixin, TimestampedMixin
from app.adapters.database.utils import make_pg_enum
from app.domain.entities.movie import MovieGenre


class UserTable(BaseTable, TimestampedMixin, IdentifableMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class MovieTable(BaseTable, TimestampedMixin, IdentifableMixin):
    __tablename__ = "movies"
    __table_args__ = (
        Index(
            None,
            "title",
            "year",
            "director",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    director: Mapped[str] = mapped_column(String(255), nullable=False)
    genre: Mapped[MovieGenre] = mapped_column(
        make_pg_enum(MovieGenre, name="movie_genre")
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
