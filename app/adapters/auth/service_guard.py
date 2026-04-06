from app.adapters.auth.config import AuthConfig
from app.application.exceptions import (
    InvalidApiKeyException,
    MissingApiKeyException,
)


class ServiceAccessGuard:
    def __init__(
        self,
        *,
        x_api_key: str | None,
        config: AuthConfig,
    ) -> None:
        self.x_api_key = x_api_key
        self.config = config

    async def authorize(self) -> None:
        if self.x_api_key is None:
            raise MissingApiKeyException("X-API-Key header is missing")

        if self.x_api_key != self.config.x_api_key:
            raise InvalidApiKeyException("X-API-Key is invalid")
