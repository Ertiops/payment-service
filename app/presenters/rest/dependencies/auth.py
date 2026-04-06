from typing import Final

from dishka.integrations.fastapi import FromDishka, inject
from fastapi.security import APIKeyHeader

from app.adapters.auth.service_guard import ServiceAccessGuard
from app.application.constants.auth import X_API_KEY_HEADER_NAME

X_API_KEY_HEADER: Final[APIKeyHeader] = APIKeyHeader(
    name=X_API_KEY_HEADER_NAME,
    auto_error=False,
)


@inject
async def require_service_access(
    service_access_guard: FromDishka[ServiceAccessGuard],
) -> None:
    await service_access_guard.authorize()
