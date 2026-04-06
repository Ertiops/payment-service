from os import getenv

import pytest

from app.adapters.auth.config import AuthConfig
from app.adapters.database.config import DatabaseConfig
from app.application.config import AppConfig
from app.presenters.rest.config import RestConfig


@pytest.fixture(scope="session")
def rest_config(db_config: DatabaseConfig) -> RestConfig:
    return RestConfig(
        host=getenv("APP_REST_HOST", "127.0.0.1"),
        port=int(getenv("APP_REST_PORT", 8000)),
        app=AppConfig(debug=True),
        auth=AuthConfig(x_api_key=getenv("APP_X_API_KEY", "secret")),
        database=db_config,
    )
