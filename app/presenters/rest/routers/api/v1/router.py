from fastapi import APIRouter, Depends

from app.presenters.rest.dependencies.auth import (
    X_API_KEY_HEADER,
    require_service_access,
)
from app.presenters.rest.routers.api.v1.controllers.payment import (
    router as payment_router,
)

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(X_API_KEY_HEADER), Depends(require_service_access)],
)
router.include_router(payment_router)
