# Generated with Alembic autogenerate, then reviewed for casts, checks and legacy data.
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7ab0a8efff9f"
down_revision: str | None = "9502c889ea91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "outbox",
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column(
        "outbox",
        "event_type",
        existing_type=postgresql.ENUM("payments.new", name="outbox_event_type"),
        type_=sa.String(length=64),
        existing_nullable=False,
        postgresql_using="event_type::text",
    )
    op.create_index(
        "ix_outbox_publish_due",
        "outbox",
        ["status", "available_at", "created_at"],
        unique=False,
    )
    op.add_column(
        "payments",
        sa.Column(
            "processing_status", sa.String(32), server_default="ready", nullable=False
        ),
    )
    op.add_column(
        "payments",
        sa.Column(
            "processing_attempts", sa.Integer(), server_default="0", nullable=False
        ),
    )
    op.add_column(
        "payments",
        sa.Column(
            "notification_status",
            sa.String(32),
            server_default="not_sent",
            nullable=False,
        ),
    )
    op.add_column(
        "payments",
        sa.Column("webhook_attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "payments", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("payments", sa.Column("last_error", sa.String(2000), nullable=True))
    op.add_column("payments", sa.Column("claim_token", sa.UUID(), nullable=True))
    op.add_column(
        "payments", sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        "ix_payments_recovery",
        "payments",
        ["processing_status", "lease_until"],
        unique=False,
    )
    op.create_check_constraint(
        op.f("ck__payments__processing_attempts_range"),
        "payments",
        "processing_attempts BETWEEN 0 AND 3",
    )
    op.create_check_constraint(
        op.f("ck__payments__webhook_attempts_range"),
        "payments",
        "webhook_attempts BETWEEN 0 AND processing_attempts",
    )
    # The previous version did not persist delivery evidence. Never invent success.
    op.execute(
        "UPDATE payments SET notification_status = 'unknown' WHERE status <> 'pending'"
    )
    # Preserve old publication failures and make them recoverable again.
    op.execute("UPDATE outbox SET status = 'pending' WHERE status = 'failed'")


def downgrade() -> None:
    unsupported = op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM outbox WHERE event_type <> 'payments.new')"
        )
    )
    if unsupported:
        raise RuntimeError("Drain retry/DLQ outbox records before downgrading")
    op.drop_constraint(
        op.f("ck__payments__webhook_attempts_range"), "payments", type_="check"
    )
    op.drop_constraint(
        op.f("ck__payments__processing_attempts_range"), "payments", type_="check"
    )
    op.drop_index("ix_payments_recovery", table_name="payments")
    op.drop_column("payments", "lease_until")
    op.drop_column("payments", "claim_token")
    op.drop_column("payments", "last_error")
    op.drop_column("payments", "delivered_at")
    op.drop_column("payments", "webhook_attempts")
    op.drop_column("payments", "notification_status")
    op.drop_column("payments", "processing_attempts")
    op.drop_column("payments", "processing_status")
    op.drop_index("ix_outbox_publish_due", table_name="outbox")
    op.alter_column(
        "outbox",
        "event_type",
        existing_type=sa.String(64),
        type_=postgresql.ENUM("payments.new", name="outbox_event_type"),
        existing_nullable=False,
        postgresql_using="event_type::outbox_event_type",
    )
    op.drop_column("outbox", "available_at")
