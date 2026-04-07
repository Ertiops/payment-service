from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.database.base import BaseTable, IdentifableMixin, TimestampedMixin
from app.adapters.database.utils import make_pg_enum
from app.domain.entities.outbox import OutboxEventType, OutboxStatus
from app.domain.entities.payment import (
    PaymentCurrency,
    PaymentStatus,
)


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


class OutboxTable(BaseTable, TimestampedMixin, IdentifableMixin):
    __tablename__ = "outbox"

    event_type: Mapped[OutboxEventType] = mapped_column(
        make_pg_enum(OutboxEventType, name="outbox_event_type"),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        make_pg_enum(OutboxStatus, name="outbox_status"),
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
