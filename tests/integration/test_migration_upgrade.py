from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from sqlalchemy import Connection, inspect, text

from app.adapters.database.config import DatabaseConfig
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


async def test_head_round_trip_preserves_schema(
    migration_database: DurableDatabase,
    alembic_config: Config,
) -> None:
    async with migration_database.engine.begin() as connection:
        await connection.run_sync(change_revision, alembic_config, "head", False)
        await connection.run_sync(
            change_revision,
            alembic_config,
            "9502c889ea91",
            True,
        )
        await connection.run_sync(change_revision, alembic_config, "head", False)
        checks = await connection.run_sync(
            lambda conn: inspect(conn).get_check_constraints("payments")
        )
        version = await connection.scalar(
            text("SELECT version_num FROM alembic_version")
        )
    assert (version, sorted(item["name"] for item in checks)) == (
        "7ab0a8efff9f",
        [
            "ck__payments__processing_attempts_range",
            "ck__payments__webhook_attempts_range",
        ],
    )


async def test_legacy_delivery_is_unknown_and_failed_publication_is_recoverable(
    migration_database: DurableDatabase,
    alembic_config: Config,
) -> None:
    async with migration_database.engine.begin() as connection:
        await connection.run_sync(
            change_revision,
            alembic_config,
            "9502c889ea91",
            False,
        )
        await connection.execute(
            text(
                "INSERT INTO payments "
                "(id, amount, currency, description, meta_data, status, "
                "idempotency_key, "
                "webhook_url, processed_at) VALUES "
                "(:id, 10.50, 'USD', 'legacy', '{}', 'succeeded', 'legacy-key', "
                "'https://example.invalid/webhook', now())"
            ),
            {"id": uuid4()},
        )
        await connection.execute(
            text(
                "INSERT INTO outbox "
                "(id, event_type, payload, status, attempts, last_error) "
                "VALUES (:id, 'payments.new', '{}', 'failed', 3, 'old broker failure')"
            ),
            {"id": uuid4()},
        )
        await connection.run_sync(change_revision, alembic_config, "head", False)
        payment = (
            await connection.execute(
                text(
                    "SELECT status, notification_status, "
                    "webhook_attempts, delivered_at "
                    "FROM payments"
                )
            )
        ).one()
        outbox = (
            await connection.execute(
                text("SELECT status, attempts, last_error FROM outbox")
            )
        ).one()
    assert (tuple(payment), tuple(outbox)) == (
        ("succeeded", "unknown", 0, None),
        ("pending", 3, "old broker failure"),
    )


async def test_downgrade_refuses_to_discard_retry_envelopes(
    migration_database: DurableDatabase,
    alembic_config: Config,
) -> None:
    async with migration_database.engine.begin() as connection:
        await connection.run_sync(change_revision, alembic_config, "head", False)
        await connection.execute(
            text(
                "INSERT INTO outbox (id, event_type, payload, status, attempts) "
                "VALUES (:id, 'payments.retry.1', '{}', 'pending', 0)"
            ),
            {"id": uuid4()},
        )
        with pytest.raises(RuntimeError):
            await connection.run_sync(
                change_revision,
                alembic_config,
                "9502c889ea91",
                True,
            )
