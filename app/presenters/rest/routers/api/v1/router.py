from fastapi import APIRouter

from app.presenters.rest.routers.api.v1.controllers.movie import (
    router as movie_router,
)
from app.presenters.rest.routers.api.v1.controllers.user import (
    router as user_router,
)

router = APIRouter(prefix="/v1")
router.include_router(user_router)
router.include_router(movie_router)
