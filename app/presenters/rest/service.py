import logging
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from typing import Any, Final

from aiomisc.service.uvicorn import UvicornApplication, UvicornService
from dishka import Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.database.di import DatabaseProvider
from app.application.exceptions import (
    AppException,
    EmptyPayloadException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
)
from app.domain.di import DomainProvider
from app.presenters.rest.config import RestConfig
from app.presenters.rest.routers.api.router import router as api_router
from app.presenters.rest.routers.api.v1.exception_handlers import (
    app_exception_handler,
    empty_payload_exception_handler,
    entity_already_exists_exception_handler,
    entity_not_found_exception_handler,
    http_exception_handler,
)

log = logging.getLogger(__name__)


ExceptionHandlersType = tuple[tuple[type[Exception], Callable], ...]

EXCEPTION_HANDLERS: Final[ExceptionHandlersType] = (
    (HTTPException, http_exception_handler),
    (AppException, app_exception_handler),
    (EntityNotFoundException, entity_not_found_exception_handler),
    (EmptyPayloadException, empty_payload_exception_handler),
    (EntityAlreadyExistsException, entity_already_exists_exception_handler),
)


class RestService(UvicornService):
    config: RestConfig

    def __init__(self, *, extra_providers: Sequence[Provider] = (), **kwargs: Any):
        self.extra_providers = extra_providers
        super().__init__(**kwargs)

    async def create_application(self) -> UvicornApplication:
        self.__app = FastAPI(
            debug=self.config.app.debug,
            title=self.config.app.title,
            description=self.config.app.description,
            version=self.config.app.version,
            openapi_url="/docs/openapi.json",
            docs_url="/docs/swagger",
            redoc_url="/docs/redoc",
            lifespan=lifespan,
        )

        self.set_middlewares()
        self.set_routes()
        self.set_exceptions()
        self.set_dependencies()

        log.info("REST service app configured")
        return self.__app

    def set_middlewares(self) -> None:
        self.__app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def set_routes(self) -> None:
        self.__app.include_router(api_router)

    def set_exceptions(self) -> None:
        for exception, handler in EXCEPTION_HANDLERS:
            self.__app.add_exception_handler(exception, handler)

    def set_dependencies(self) -> None:
        container = make_async_container(
            DatabaseProvider(
                dsn=self.config.database.dsn,
                debug=self.config.app.debug,
            ),
            DomainProvider(),
            *self.extra_providers,
        )
        setup_dishka(container=container, app=self.__app)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.dishka_container.close()
