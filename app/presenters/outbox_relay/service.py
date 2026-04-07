import asyncio
import logging
from contextlib import suppress

from aiomisc import Service
from dishka import make_async_container
from dishka.async_container import AsyncContainer

from app.adapters.database.di import DatabaseProvider
from app.adapters.rabbitmq.di import RabbitMQProvider
from app.domain.di import OutboxRelayProvider
from app.domain.entities.outbox import (
    OutboxEventType,
    PublishNextOutbox,
)
from app.domain.use_cases.outbox.publish_next import PublishNextOutboxUC
from app.presenters.outbox_relay.config import OutboxRelayConfig

log = logging.getLogger(__name__)


class OutboxRelayService(Service):
    _config: OutboxRelayConfig
    _container: AsyncContainer
    _task: asyncio.Task[None]

    def __init__(self, config: OutboxRelayConfig) -> None:
        super().__init__()
        self._config = config

    async def start(self) -> None:
        self._container = make_async_container(
            DatabaseProvider(
                dsn=self._config.database.dsn,
                debug=self._config.app.debug,
            ),
            RabbitMQProvider(config=self._config.rabbitmq),
            OutboxRelayProvider(),
        )
        self._task = asyncio.create_task(self.run())
        self.start_event.set()

    async def run(self) -> None:
        while True:
            try:
                async with self._container() as request_container:
                    use_case = await request_container.get(PublishNextOutboxUC)
                    await use_case.execute(
                        input_dto=PublishNextOutbox(
                            event_type=OutboxEventType.PAYMENT_CREATED,
                            max_attempts=self._config.max_attempts,
                        )
                    )
            except Exception:
                log.exception("Outbox relay iteration failed")
            await asyncio.sleep(self._config.poll_interval)

    async def stop(self, exception: Exception | None = None) -> None:
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        await self._container.close(exception=exception)
