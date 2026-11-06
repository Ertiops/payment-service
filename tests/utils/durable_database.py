from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.schema import CreateSchema, DropSchema

from app.adapters.database.tables import BaseTable
from app.adapters.database.utils import create_engine, create_sessionmaker


@dataclass(frozen=True)
class DurableDatabase:
    engine: AsyncEngine
    sessions: async_sessionmaker[AsyncSession]


@asynccontextmanager
async def durable_database(
    dsn: str, initialize: bool = True
) -> AsyncIterator[DurableDatabase]:
    schema = "payment_test_" + uuid4().hex
    async with create_engine(dsn=dsn, debug=False) as admin:
        async with admin.begin() as connection:
            await connection.execute(CreateSchema(schema))
        try:
            async with create_engine(
                dsn=dsn,
                debug=False,
                connect_args={"server_settings": {"search_path": schema}},
            ) as engine:
                if initialize:
                    async with engine.begin() as connection:
                        await connection.run_sync(BaseTable.metadata.create_all)
                yield DurableDatabase(
                    engine=engine, sessions=create_sessionmaker(engine)
                )
        finally:
            async with admin.begin() as connection:
                await connection.execute(DropSchema(schema, cascade=True))


@asynccontextmanager
async def runtime_database(dsn: str) -> AsyncIterator[str]:
    url = make_url(dsn)
    if url.host not in ("127.0.0.1", "localhost") or not (
        url.database and url.database.startswith("payment_")
    ):
        raise ValueError("Runtime tests require a local disposable payment_* database")
    name = "payment_runtime_" + uuid4().hex
    admin = create_async_engine(dsn, isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{name}"'))
        try:
            yield url.set(database=name).render_as_string(hide_password=False)
        finally:
            async with admin.connect() as connection:
                await connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    finally:
        await admin.dispose()
