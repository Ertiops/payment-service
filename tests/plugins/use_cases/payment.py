import pytest

from app.domain.entities.payment import PaymentStatus, ProcessPayment
from app.domain.entities.webhook import SendPaymentWebhook
from app.domain.interfaces.gateways.payment import IPaymentGateway
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.interfaces.webhooks.payment import IPaymentWebhookSender
from app.domain.uow import AbstractUow
from app.domain.use_cases.payment.create import CreatePaymentUC
from app.domain.use_cases.payment.get_by_id import GetPaymentByIdUC
from app.domain.use_cases.payment.process import ProcessPaymentUC


class FakePaymentGateway(IPaymentGateway):
    def __init__(self) -> None:
        self.status = PaymentStatus.SUCCEEDED
        self.inputs: list[ProcessPayment] = []

    async def process(self, *, input_dto: ProcessPayment) -> PaymentStatus:
        self.inputs.append(input_dto)
        return self.status


class FakePaymentWebhookSender(IPaymentWebhookSender):
    def __init__(self) -> None:
        self.inputs: list[SendPaymentWebhook] = []
        self.exception: Exception | None = None

    async def send(self, *, input_dto: SendPaymentWebhook) -> None:
        if self.exception is not None:
            raise self.exception
        self.inputs.append(input_dto)


@pytest.fixture
def payment_gateway() -> FakePaymentGateway:
    return FakePaymentGateway()


@pytest.fixture
def payment_webhook_sender() -> FakePaymentWebhookSender:
    return FakePaymentWebhookSender()


@pytest.fixture
def create_payment_uc(
    uow: AbstractUow,
    payment_storage: IPaymentStorage,
    outbox_storage: IOutboxStorage,
) -> CreatePaymentUC:
    return CreatePaymentUC(
        uow=uow,
        payment_storage=payment_storage,
        outbox_storage=outbox_storage,
    )


@pytest.fixture
def get_payment_by_id_uc(
    uow: AbstractUow,
    payment_storage: IPaymentStorage,
) -> GetPaymentByIdUC:
    return GetPaymentByIdUC(
        uow=uow,
        payment_storage=payment_storage,
    )


@pytest.fixture
def process_payment_uc(
    uow: AbstractUow,
    payment_storage: IPaymentStorage,
    payment_gateway: FakePaymentGateway,
    payment_webhook_sender: FakePaymentWebhookSender,
) -> ProcessPaymentUC:
    return ProcessPaymentUC(
        uow=uow,
        payment_storage=payment_storage,
        payment_gateway=payment_gateway,
        payment_webhook_sender=payment_webhook_sender,
    )
