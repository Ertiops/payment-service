from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Float, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.database.base import BaseTable, IdentifableMixin, TimestampedMixin
from app.adapters.database.utils import make_pg_enum
from app.domain.entities.movie import MovieGenre
from app.domain.entities.payment import PaymentCurrency, PaymentStatus


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


class PaymentTable(BaseTable, TimestampedMixin, IdentifableMixin):
    __tablename__ = "payments"

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    currency: Mapped[PaymentCurrency] = mapped_column(
        make_pg_enum(PaymentCurrency, name="payment_currency"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    meta_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        make_pg_enum(PaymentStatus, name="payment_status"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    webhook_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
