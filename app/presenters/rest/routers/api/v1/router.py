from fastapi import APIRouter

from app.presenters.rest.routers.api.v1.controllers.payment import (
    router as payment_router,
)

router = APIRouter(prefix="/v1")
router.include_router(payment_router)
