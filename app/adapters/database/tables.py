from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.database.base import BaseTable as BaseTable
from app.adapters.database.base import IdentifableMixin, TimestampedMixin
from app.adapters.database.utils import make_pg_enum
from app.domain.entities.outbox import OutboxStatus
from app.domain.entities.payment import (
    PaymentCurrency,
    PaymentStatus,
)


class PaymentTable(BaseTable, TimestampedMixin, IdentifableMixin):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "processing_attempts BETWEEN 0 AND 3", name="processing_attempts_range"
        ),
        CheckConstraint(
            "webhook_attempts BETWEEN 0 AND processing_attempts",
            name="webhook_attempts_range",
        ),
        Index("ix_payments_recovery", "processing_status", "lease_until"),
    )

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
    processing_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="ready"
    )
    processing_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    notification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="not_sent"
    )
    webhook_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(2000))
    claim_token: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OutboxTable(BaseTable, TimestampedMixin, IdentifableMixin):
    __tablename__ = "outbox"
    __table_args__ = (
        Index("ix_outbox_publish_due", "status", "available_at", "created_at"),
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
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
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
