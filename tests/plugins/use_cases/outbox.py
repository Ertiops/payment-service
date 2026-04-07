import pytest

from app.domain.entities.outbox import PublishOutboxMessage
from app.domain.interfaces.publishers.outbox import IOutboxPublisher
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.outbox.publish_next import PublishNextOutboxUC


class FakeOutboxPublisher(IOutboxPublisher):
    def __init__(self) -> None:
        self.messages: list[PublishOutboxMessage] = []
        self.exception: Exception | None = None

    async def publish(self, *, input_dto: PublishOutboxMessage) -> None:
        if self.exception is not None:
            raise self.exception
        self.messages.append(input_dto)


@pytest.fixture
def outbox_publisher() -> FakeOutboxPublisher:
    return FakeOutboxPublisher()


@pytest.fixture
def publish_next_outbox_uc(
    uow: AbstractUow,
    outbox_storage: IOutboxStorage,
    outbox_publisher: FakeOutboxPublisher,
) -> PublishNextOutboxUC:
    return PublishNextOutboxUC(
        uow=uow,
        outbox_storage=outbox_storage,
        outbox_publisher=outbox_publisher,
    )
