from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.converters.payment import convert_payment_table_to_dto
from app.adapters.database.payment_queries import (
    claim_conditions,
    claim_values,
    completion_values,
    expired_attempt_conditions,
    gateway_result_conditions,
    key_conditions,
    live_claim_conditions,
    recovery_conditions,
    webhook_start_conditions,
)
from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import (
    ClaimPaymentAttempt,
    CompletePaymentAttempt,
    CreatePayment,
    ExpiredPaymentAttempt,
    GetPaymentByKey,
    NotificationStatus,
    Payment,
    PaymentClaim,
    PaymentStatus,
    RecoverPaymentAttempt,
    SaveGatewayResult,
)
from app.domain.interfaces.storages.payment import IPaymentStorage


class PaymentStorage(IPaymentStorage):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_if_absent(self, *, input_dto: CreatePayment) -> Payment | None:
        stmt = (
            insert(PaymentTable)
            .values(
                amount=input_dto.amount,
                currency=input_dto.currency,
                description=input_dto.description,
                meta_data=input_dto.meta_data,
                status=PaymentStatus.PENDING,
                idempotency_key=input_dto.idempotency_key,
                webhook_url=input_dto.webhook_url,
            )
            .on_conflict_do_nothing(index_elements=[PaymentTable.idempotency_key])
            .returning(PaymentTable)
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def get_by_key(self, *, input_dto: GetPaymentByKey) -> Payment | None:
        stmt = select(PaymentTable).where(*key_conditions(input_dto))
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def claim_attempt(self, *, input_dto: ClaimPaymentAttempt) -> Payment | None:
        stmt = (
            update(PaymentTable)
            .where(*claim_conditions(input_dto))
            .values(**claim_values(input_dto))
            .returning(PaymentTable)
            .execution_options(populate_existing=True)
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def save_gateway_result(
        self, *, input_dto: SaveGatewayResult
    ) -> Payment | None:
        stmt = (
            update(PaymentTable)
            .where(*gateway_result_conditions(input_dto))
            .values(status=input_dto.status, processed_at=input_dto.processed_at)
            .returning(PaymentTable)
            .execution_options(populate_existing=True)
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def start_webhook(self, *, input_dto: PaymentClaim) -> Payment | None:
        stmt = (
            update(PaymentTable)
            .where(*webhook_start_conditions(input_dto))
            .values(
                notification_status=NotificationStatus.SENDING,
                webhook_attempts=PaymentTable.webhook_attempts + 1,
            )
            .returning(PaymentTable)
            .execution_options(populate_existing=True)
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def complete_attempt(
        self, *, input_dto: CompletePaymentAttempt
    ) -> Payment | None:
        stmt = (
            update(PaymentTable)
            .where(*live_claim_conditions(input_dto))
            .values(**completion_values(input_dto))
            .returning(PaymentTable)
            .execution_options(populate_existing=True)
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def get_expired_attempt(
        self, *, input_dto: RecoverPaymentAttempt
    ) -> ExpiredPaymentAttempt | None:
        stmt = (
            select(PaymentTable)
            .where(*expired_attempt_conditions(input_dto))
            .order_by(PaymentTable.lease_until)
            .limit(1)
            .with_for_update(skip_locked=True)
            .execution_options(populate_existing=True)
        )
        result = await self.session.scalar(stmt)
        if result is None or result.claim_token is None:
            return None
        return ExpiredPaymentAttempt(
            payment=convert_payment_table_to_dto(result=result),
            token=result.claim_token,
        )

    async def recover_attempt(
        self, *, input_dto: CompletePaymentAttempt
    ) -> Payment | None:
        stmt = (
            update(PaymentTable)
            .where(*recovery_conditions(input_dto))
            .values(**completion_values(input_dto))
            .returning(PaymentTable)
            .execution_options(populate_existing=True)
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def get_by_id(self, *, input_dto: UUID) -> Payment | None:
        stmt = select(PaymentTable).where(
            PaymentTable.id == input_dto,
            PaymentTable.deleted_at.is_(None),
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None
