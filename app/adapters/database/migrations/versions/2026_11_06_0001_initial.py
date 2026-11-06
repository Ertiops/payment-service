# Generated with Alembic autogenerate against an empty PostgreSQL database.
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outbox",
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "published", "failed", name="outbox_status"),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=2000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__outbox")),
    )
    op.create_index(
        "ix_outbox_publish_due",
        "outbox",
        ["status", "available_at", "created_at"],
        unique=False,
    )
    op.create_table(
        "payments",
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "currency",
            postgresql.ENUM("RUB", "USD", "EUR", name="payment_currency"),
            nullable=False,
        ),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("meta_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "succeeded", "failed", name="payment_status"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("webhook_url", sa.String(length=2048), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "processing_status",
            sa.String(length=32),
            server_default="ready",
            nullable=False,
        ),
        sa.Column(
            "processing_attempts", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "notification_status",
            sa.String(length=32),
            server_default="not_sent",
            nullable=False,
        ),
        sa.Column("webhook_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=2000), nullable=True),
        sa.Column("claim_token", sa.UUID(), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "processing_attempts BETWEEN 0 AND 3",
            name=op.f("ck__payments__processing_attempts_range"),
        ),
        sa.CheckConstraint(
            "webhook_attempts BETWEEN 0 AND processing_attempts",
            name=op.f("ck__payments__webhook_attempts_range"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__payments")),
        sa.UniqueConstraint(
            "idempotency_key", name=op.f("uq__payments__idempotency_key")
        ),
    )
    op.create_index(
        "ix_payments_recovery",
        "payments",
        ["processing_status", "lease_until"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_payments_recovery", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_outbox_publish_due", table_name="outbox")
    op.drop_table("outbox")
    for name in ("payment_status", "payment_currency", "outbox_status"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=False)
