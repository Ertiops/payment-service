from typing import NoReturn
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.converters.payment import convert_payment_table_to_dto
from app.adapters.database.tables import PaymentTable
from app.application.exceptions import (
    EntityAlreadyExistsException,
    EntityNotFoundException,
    StorageException,
)
from app.domain.entities.payment import (
    CreatePayment,
    Payment,
    PaymentStatus,
    UpdatePayment,
)
from app.domain.interfaces.storages.payment import IPaymentStorage


class PaymentStorage(IPaymentStorage):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, input_dto: CreatePayment) -> Payment:
        stmt = (
            insert(PaymentTable)
            .values(
                amount=input_dto.amount,
                currency=input_dto.currency,
                description=input_dto.description,
                meta_data=input_dto.meta_data,
                status=input_dto.status,
                idempotency_key=input_dto.idempotency_key,
                webhook_url=input_dto.webhook_url,
            )
            .returning(PaymentTable)
        )
        try:
            result = (await self.session.scalars(stmt)).one()
        except IntegrityError as e:
            self._raise_exception(e)
        return convert_payment_table_to_dto(result=result)

    async def get_by_id(self, *, input_dto: UUID) -> Payment | None:
        stmt = select(PaymentTable).where(
            PaymentTable.id == input_dto,
            PaymentTable.deleted_at.is_(None),
        )
        result = await self.session.scalar(stmt)
        return convert_payment_table_to_dto(result=result) if result else None

    async def update_by_id(self, *, input_dto: UpdatePayment) -> Payment:
        stmt = (
            update(PaymentTable)
            .where(
                PaymentTable.id == input_dto.id,
                PaymentTable.status == PaymentStatus.PENDING,
                PaymentTable.deleted_at.is_(None),
            )
            .values(**input_dto.to_dict())
            .returning(PaymentTable)
        )
        try:
            result = (await self.session.scalars(stmt)).one()
        except NoResultFound as e:
            raise EntityNotFoundException(
                entity=Payment,
                entity_id=input_dto.id,
            ) from e
        return convert_payment_table_to_dto(result=result)

    def _raise_exception(self, e: DBAPIError) -> NoReturn:
        constraint = e.__cause__.__cause__.constraint_name  # type: ignore[union-attr]
        if constraint == "uq__payments__idempotency_key":
            raise EntityAlreadyExistsException(
                "Payment with this idempotency key already exists"
            ) from e
        raise StorageException(self.__class__.__name__) from e
