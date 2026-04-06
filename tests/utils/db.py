from typing import Final

from alembic.autogenerate import compare_metadata
from alembic.config import Config as AlembicConfig
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, MetaData, pool, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_engine_from_config,
)

TRUNCATE_TABLE_SQL: Final[str] = """
DO $$
DECLARE
    stmt text;
BEGIN
    PERFORM pg_advisory_lock(424242);

    SELECT
        'TRUNCATE TABLE ' ||
        string_agg(format('%I.%I', schemaname, tablename), ', ') ||
        ' RESTART IDENTITY CASCADE'
    INTO stmt
    FROM pg_tables
    WHERE schemaname = '{schema}'
      AND tablename <> 'alembic_version';

    IF stmt IS NOT NULL THEN
        EXECUTE stmt;
    END IF;

    PERFORM pg_advisory_unlock(424242);

EXCEPTION
    WHEN UNDEFINED_TABLE THEN
        PERFORM pg_advisory_unlock(424242);
        NULL;
END $$;
"""


async def truncate_tables(engine: AsyncEngine, schema_name: str) -> None:
    async with engine.connect() as connection:
        await connection.execute(text(TRUNCATE_TABLE_SQL.format(schema=schema_name)))


async def run_async_migrations(
    config: AlembicConfig,
    target_metadata: MetaData,
    revision: str,
    engine: AsyncEngine | None = None,
) -> None:
    script = ScriptDirectory.from_config(config)

    def upgrade(rev, context):
        return script._upgrade_revs(revision, rev)

    if engine is None:
        engine = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            poolclass=pool.NullPool,
        )

    with EnvironmentContext(
        config,
        script=script,
        fn=upgrade,
        as_sql=False,
        starting_rev=None,
        destination_rev=revision,
    ) as context:
        async with engine.connect() as connection:
            await connection.run_sync(
                _do_run_migrations,
                target_metadata=target_metadata,
                context=context,
            )
            await connection.commit()


def _do_run_migrations(
    connection: Connection,
    target_metadata: MetaData,
    context: EnvironmentContext,
) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def get_diff_db_metadata(connection: Connection, metadata: MetaData):
    migration_ctx = MigrationContext.configure(connection)
    return compare_metadata(context=migration_ctx, metadata=metadata)
