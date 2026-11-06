from app.application.use_case import IUseCase
from app.domain.entities.payment import Payment, RecoverPaymentAttempt
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.payment.workflow import failed_attempt, processing_message


class RecoverPaymentAttemptUC(IUseCase[RecoverPaymentAttempt, Payment | None]):
    def __init__(
        self,
        uow: AbstractUow,
        payment_storage: IPaymentStorage,
        outbox_storage: IOutboxStorage,
    ) -> None:
        self._uow = uow
        self._payment_storage = payment_storage
        self._outbox_storage = outbox_storage

    async def execute(self, *, input_dto: RecoverPaymentAttempt) -> Payment | None:
        async with self._uow:
            expired = await self._payment_storage.get_expired_attempt(
                input_dto=input_dto
            )
            if expired is None:
                return None
            payment = await self._payment_storage.recover_attempt(
                input_dto=failed_attempt(
                    expired.payment, expired.token, "AttemptExpired: outcome unknown"
                )
            )
            if payment is not None:
                await self._outbox_storage.create(
                    input_dto=processing_message(
                        payment.id, payment.processing_attempts + 1
                    )
                )
            return payment
