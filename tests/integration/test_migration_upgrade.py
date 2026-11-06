from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Connection, inspect, text
from sqlalchemy.exc import IntegrityError

from app.adapters.database.config import DatabaseConfig
from app.adapters.database.tables import BaseTable
from tests.utils.durable_database import DurableDatabase, durable_database


@pytest.fixture
async def migration_database(
    db_config: DatabaseConfig,
) -> AsyncIterator[DurableDatabase]:
    async with durable_database(db_config.dsn, initialize=False) as database:
        yield database


def change_revision(
    connection: Connection,
    config: Config,
    revision: str,
    backwards: bool,
) -> None:
    config.attributes["connection"] = connection
    try:
        if backwards:
            downgrade(config, revision)
        else:
            upgrade(config, revision)
    finally:
        config.attributes.pop("connection", None)


def schema_diff(connection: Connection) -> list[object]:
    context = MigrationContext.configure(
        connection, opts={"compare_server_default": True}
    )
    return compare_metadata(context, BaseTable.metadata)


async def test_initial_migration_round_trip_preserves_schema(
    migration_database: DurableDatabase,
    alembic_config: Config,
) -> None:
    async with migration_database.engine.begin() as connection:
        await connection.run_sync(change_revision, alembic_config, "head", False)
        await connection.run_sync(change_revision, alembic_config, "base", True)
        tables_after_downgrade = await connection.run_sync(
            lambda conn: inspect(conn).get_table_names()
        )
        enums_after_downgrade = (
            (
                await connection.execute(
                    text(
                        "SELECT t.typname FROM pg_type t "
                        "JOIN pg_namespace n ON n.oid = t.typnamespace "
                        "WHERE t.typtype = 'e' AND n.nspname = current_schema() "
                        "ORDER BY t.typname"
                    )
                )
            )
            .scalars()
            .all()
        )
        await connection.run_sync(change_revision, alembic_config, "head", False)
        diff = await connection.run_sync(schema_diff)
        checks = await connection.run_sync(
            lambda conn: inspect(conn).get_check_constraints("payments")
        )
        version = await connection.scalar(
            text("SELECT version_num FROM alembic_version")
        )
    assert (
        tables_after_downgrade,
        enums_after_downgrade,
        version,
        diff,
        sorted(item["name"] for item in checks),
    ) == (
        ["alembic_version"],
        [],
        "0001",
        [],
        [
            "ck__payments__processing_attempts_range",
            "ck__payments__webhook_attempts_range",
        ],
    )


async def test_initial_schema_sets_workflow_defaults_and_accepts_retry_events(
    migration_database: DurableDatabase,
    alembic_config: Config,
) -> None:
    async with migration_database.engine.begin() as connection:
        await connection.run_sync(change_revision, alembic_config, "head", False)
        await connection.execute(
            text(
                "INSERT INTO payments "
                "(id, amount, currency, description, meta_data, status, "
                "idempotency_key, webhook_url) VALUES "
                "(:id, 10.50, 'USD', 'initial', '{}', 'pending', 'initial-key', "
                "'https://example.invalid/webhook')"
            ),
            {"id": uuid4()},
        )
        await connection.execute(
            text(
                "INSERT INTO outbox (id, event_type, payload, status, attempts) "
                "VALUES (:id, 'payments.retry.1', '{}', 'pending', 0)"
            ),
            {"id": uuid4()},
        )
        payment = (
            await connection.execute(
                text(
                    "SELECT processing_status, processing_attempts, "
                    "notification_status, webhook_attempts, "
                    "delivered_at, last_error, claim_token, lease_until "
                    "FROM payments"
                )
            )
        ).one()
        outbox = (
            await connection.execute(
                text(
                    "SELECT event_type, status, attempts, last_error, "
                    "published_at, available_at IS NOT NULL FROM outbox"
                )
            )
        ).one()
    assert (tuple(payment), tuple(outbox)) == (
        ("ready", 0, "not_sent", 0, None, None, None, None),
        ("payments.retry.1", "pending", 0, None, None, True),
    )


@pytest.mark.parametrize(
    ("processing_attempts", "webhook_attempts", "constraint"),
    [
        (-1, 0, "processing_attempts_range"),
        (4, 0, "processing_attempts_range"),
        (1, -1, "webhook_attempts_range"),
        (0, 1, "webhook_attempts_range"),
    ],
)
async def test_initial_schema_enforces_attempt_budget(
    migration_database: DurableDatabase,
    alembic_config: Config,
    processing_attempts: int,
    webhook_attempts: int,
    constraint: str,
) -> None:
    with pytest.raises(IntegrityError, match=constraint):
        async with migration_database.engine.begin() as connection:
            await connection.run_sync(change_revision, alembic_config, "head", False)
            await connection.execute(
                text(
                    "INSERT INTO payments "
                    "(id, amount, currency, description, meta_data, status, "
                    "idempotency_key, webhook_url, processing_attempts, "
                    "webhook_attempts) VALUES "
                    "(:id, 10.50, 'USD', 'initial', '{}', 'pending', 'budget-key', "
                    "'https://example.invalid/webhook', "
                    ":processing_attempts, :webhook_attempts)"
                ),
                {
                    "id": uuid4(),
                    "processing_attempts": processing_attempts,
                    "webhook_attempts": webhook_attempts,
                },
            )
