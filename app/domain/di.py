from dishka import Provider, Scope, provide

from app.domain.interfaces.gateways.payment import IPaymentGateway
from app.domain.interfaces.publishers.outbox import IOutboxPublisher
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.interfaces.webhooks.payment import IPaymentWebhookSender
from app.domain.processing import ProcessingConfig
from app.domain.uow import AbstractUow
from app.domain.use_cases.outbox.publish_next import PublishNextOutboxUC
from app.domain.use_cases.payment.create import CreatePaymentUC
from app.domain.use_cases.payment.get_by_id import GetPaymentByIdUC
from app.domain.use_cases.payment.process import ProcessPaymentUC
from app.domain.use_cases.payment.recover import RecoverPaymentAttemptUC


class DomainProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def create_payment(
        self,
        payment_storage: IPaymentStorage,
        outbox_storage: IOutboxStorage,
        uow: AbstractUow,
    ) -> CreatePaymentUC:
        return CreatePaymentUC(
            payment_storage=payment_storage,
            outbox_storage=outbox_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def get_payment_by_id(
        self,
        payment_storage: IPaymentStorage,
        uow: AbstractUow,
    ) -> GetPaymentByIdUC:
        return GetPaymentByIdUC(
            payment_storage=payment_storage,
            uow=uow,
        )


class OutboxRelayProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def recover_payment_attempt(
        self,
        payment_storage: IPaymentStorage,
        outbox_storage: IOutboxStorage,
        uow: AbstractUow,
    ) -> RecoverPaymentAttemptUC:
        return RecoverPaymentAttemptUC(
            uow=uow,
            payment_storage=payment_storage,
            outbox_storage=outbox_storage,
        )

    @provide(scope=Scope.REQUEST)
    def publish_next_outbox(
        self,
        outbox_storage: IOutboxStorage,
        outbox_publisher: IOutboxPublisher,
        uow: AbstractUow,
    ) -> PublishNextOutboxUC:
        return PublishNextOutboxUC(
            uow=uow,
            outbox_storage=outbox_storage,
            outbox_publisher=outbox_publisher,
        )


class PaymentConsumerProvider(Provider):
    def __init__(self, config: ProcessingConfig) -> None:
        super().__init__()
        self._config = config

    @provide(scope=Scope.APP)
    def processing_config(self) -> ProcessingConfig:
        return self._config

    @provide(scope=Scope.REQUEST)
    def process_payment(
        self,
        payment_storage: IPaymentStorage,
        outbox_storage: IOutboxStorage,
        payment_gateway: IPaymentGateway,
        payment_webhook_sender: IPaymentWebhookSender,
        uow: AbstractUow,
        config: ProcessingConfig,
    ) -> ProcessPaymentUC:
        return ProcessPaymentUC(
            uow=uow,
            payment_storage=payment_storage,
            outbox_storage=outbox_storage,
            payment_gateway=payment_gateway,
            payment_webhook_sender=payment_webhook_sender,
            config=config,
        )
