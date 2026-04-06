from dishka import Provider, Scope, provide
from starlette.requests import Request

from app.adapters.auth.config import AuthConfig
from app.adapters.auth.service_guard import ServiceAccessGuard
from app.application.constants.auth import X_API_KEY_HEADER_NAME


class AuthProvider(Provider):
    def __init__(self, config: AuthConfig) -> None:
        super().__init__()
        self._config = config

    @provide(scope=Scope.REQUEST)
    def x_api_key(self, request: Request) -> str | None:
        return request.headers.get(X_API_KEY_HEADER_NAME)

    @provide(scope=Scope.REQUEST)
    def service_access_guard(
        self,
        *,
        x_api_key: str | None,
    ) -> ServiceAccessGuard:
        return ServiceAccessGuard(
            x_api_key=x_api_key,
            config=self._config,
        )
