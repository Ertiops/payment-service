from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

import pytest
from aiomisc.service.uvicorn import UvicornApplication
from httpx import URL, ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.presenters.rest.config import RestConfig
from app.presenters.rest.service import RestService
from tests.plugins.instances.database.uow import TEST_SESSIONS, TestDBProvider
from tests.utils.worker import get_worker_name


@pytest.fixture(scope="session")
def rest_base_url() -> URL:
    return URL(scheme="http", host="127.0.0.1", port=8000)


@pytest.fixture(scope="session")
async def test_app(
    rest_config: RestConfig, rest_base_url: URL, test_db_provider: TestDBProvider
) -> UvicornApplication:
    service = RestService(
        host=rest_base_url.host,
        port=rest_base_url.port,
        config=rest_config,
        extra_providers=[test_db_provider],
    )
    return await service.create_application()


@pytest.fixture(scope="session")
async def client_context(
    test_app: UvicornApplication, rest_base_url: URL
) -> AsyncGenerator[AsyncClient, Any]:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url=rest_base_url
    ) as client:
        yield client


@pytest.fixture
async def client(
    client_context: AsyncClient, session: AsyncSession
) -> AsyncIterator[AsyncClient]:
    worker_name = get_worker_name()
    TEST_SESSIONS[worker_name] = session
    try:
        yield client_context
    finally:
        del TEST_SESSIONS[worker_name]
