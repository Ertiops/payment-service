import pytest

from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.payment.create import CreatePaymentUC
from app.domain.use_cases.payment.get_by_id import GetPaymentByIdUC


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
