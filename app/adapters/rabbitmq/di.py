from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from faststream.rabbit import RabbitBroker
from faststream.rabbit.schemas.channel import Channel

from app.adapters.rabbitmq.config import RabbitMQConfig
from app.adapters.rabbitmq.publishers.outbox import RabbitMQOutboxPublisher
from app.adapters.rabbitmq.topology import declare_payment_topology
from app.domain.interfaces.publishers.outbox import IOutboxPublisher


class RabbitMQProvider(Provider):
    def __init__(self, config: RabbitMQConfig) -> None:
        super().__init__()
        self._config = config

    @provide(scope=Scope.APP)
    async def rabbit_broker(self) -> AsyncIterator[RabbitBroker]:
        broker = RabbitBroker(
            self._config.dsn,
            default_channel=Channel(publisher_confirms=True, on_return_raises=True),
        )
        await broker.start()
        try:
            await declare_payment_topology(broker, self._config)
            yield broker
        finally:
            await broker.stop()

    @provide(scope=Scope.REQUEST)
    def outbox_publisher(self, broker: RabbitBroker) -> IOutboxPublisher:
        return RabbitMQOutboxPublisher(broker=broker, config=self._config)
