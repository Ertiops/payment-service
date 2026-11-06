from typing import Protocol
from uuid import UUID

from app.domain.entities.payment import (
    ClaimPaymentAttempt,
    CompletePaymentAttempt,
    CreatePayment,
    ExpiredPaymentAttempt,
    GetPaymentByKey,
    Payment,
    PaymentClaim,
    RecoverPaymentAttempt,
    SaveGatewayResult,
)


class IPaymentStorage(Protocol):
    async def create_if_absent(self, *, input_dto: CreatePayment) -> Payment | None: ...

    async def get_by_key(self, *, input_dto: GetPaymentByKey) -> Payment | None: ...

    async def claim_attempt(
        self, *, input_dto: ClaimPaymentAttempt
    ) -> Payment | None: ...

    async def save_gateway_result(
        self, *, input_dto: SaveGatewayResult
    ) -> Payment | None: ...

    async def start_webhook(self, *, input_dto: PaymentClaim) -> Payment | None: ...

    async def complete_attempt(
        self, *, input_dto: CompletePaymentAttempt
    ) -> Payment | None: ...

    async def get_expired_attempt(
        self, *, input_dto: RecoverPaymentAttempt
    ) -> ExpiredPaymentAttempt | None: ...

    async def recover_attempt(
        self, *, input_dto: CompletePaymentAttempt
    ) -> Payment | None: ...

    async def get_by_id(self, *, input_dto: UUID) -> Payment | None: ...
