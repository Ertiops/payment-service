from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from os import getenv
from uuid import uuid4

import pytest
from aiohttp import BasicAuth, ClientSession
from yarl import URL


@dataclass(frozen=True)
class RabbitTestContext:
    dsn: str
    vhost: str


@asynccontextmanager
async def isolated_rabbit() -> AsyncIterator[RabbitTestContext]:
    dsn = getenv("APP_TEST_RABBITMQ_DSN")
    management = getenv("APP_TEST_RABBITMQ_MANAGEMENT_URL")
    if not dsn or not management:
        pytest.skip("Real RabbitMQ requires APP_TEST_RABBITMQ_DSN and management URL")
    url = URL(dsn)
    if url.host not in ("127.0.0.1", "localhost") or URL(management).host not in (
        "127.0.0.1",
        "localhost",
    ):
        raise ValueError("Integration tests require a local disposable RabbitMQ")
    name = "payment_test_" + uuid4().hex
    auth = BasicAuth(url.user or "guest", url.password or "guest")
    async with ClientSession(auth=auth) as http:
        async with http.put(f"{management}/api/vhosts/{name}") as response:
            response.raise_for_status()
        try:
            async with http.put(
                f"{management}/api/permissions/{name}/{auth.login}",
                json={"configure": ".*", "write": ".*", "read": ".*"},
            ) as response:
                response.raise_for_status()
            yield RabbitTestContext(dsn=str(url.with_path("/" + name)), vhost=name)
        finally:
            async with http.delete(f"{management}/api/vhosts/{name}") as response:
                response.raise_for_status()
