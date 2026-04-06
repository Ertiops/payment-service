from dishka import Provider, Scope, provide

from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.payment.create import CreatePaymentUC
from app.domain.use_cases.payment.get_by_id import GetPaymentByIdUC


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
