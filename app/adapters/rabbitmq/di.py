from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from faststream.rabbit import RabbitBroker

from app.adapters.rabbitmq.config import RabbitMQConfig
from app.adapters.rabbitmq.publishers.outbox import RabbitMQOutboxPublisher
from app.domain.interfaces.publishers.outbox import IOutboxPublisher


class RabbitMQProvider(Provider):
    def __init__(self, config: RabbitMQConfig) -> None:
        super().__init__()
        self._config = config

    @provide(scope=Scope.APP)
    async def rabbit_broker(self) -> AsyncIterator[RabbitBroker]:
        broker = RabbitBroker(self._config.dsn)
        await broker.start()
        yield broker
        await broker.stop()

    @provide(scope=Scope.REQUEST)
    def outbox_publisher(self, broker: RabbitBroker) -> IOutboxPublisher:
        return RabbitMQOutboxPublisher(broker=broker)
