from collections.abc import Awaitable, Callable

import pytest

from app.application.constants.auth import X_API_KEY_HEADER_NAME
from app.application.entities import UNSET, Unset
from app.presenters.rest.config import RestConfig


@pytest.fixture
def create_auth_headers(
    rest_config: RestConfig,
) -> Callable[..., Awaitable[dict[str, str]]]:
    async def _factory(
        *,
        secret: str | Unset = UNSET,
    ) -> dict[str, str]:
        value = rest_config.auth.x_api_key if isinstance(secret, Unset) else secret
        return {
            X_API_KEY_HEADER_NAME: value,
        }

    return _factory
