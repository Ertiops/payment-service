from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Header

from app.domain.entities.payment import CreatePayment, PaymentStatus
from app.domain.use_cases.payment.create import CreatePaymentUC
from app.domain.use_cases.payment.get_by_id import GetPaymentByIdUC
from app.presenters.rest.routers.api.v1.schemas.payment import (
    CreatePaymentSchema,
    PaymentAcceptedSchema,
    PaymentSchema,
)

router = APIRouter(prefix="/payments", tags=["Payments"], route_class=DishkaRoute)


@router.post(
    "/",
    response_model=PaymentAcceptedSchema,
    status_code=HTTPStatus.ACCEPTED,
    name="Create Payment",
)
async def create(
    body: CreatePaymentSchema,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=255),
    ],
    *,
    use_case: FromDishka[CreatePaymentUC],
) -> PaymentAcceptedSchema:
    payment = await use_case.execute(
        input_dto=CreatePayment(
            amount=body.amount,
            currency=body.currency,
            description=body.description,
            meta_data=body.meta_data,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=str(body.webhook_url),
        )
    )
    return PaymentAcceptedSchema(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get(
    "/{payment_id:uuid}/",
    response_model=PaymentSchema,
    status_code=HTTPStatus.OK,
    name="Get Payment by ID",
)
async def get_by_id(
    payment_id: UUID,
    *,
    use_case: FromDishka[GetPaymentByIdUC],
) -> PaymentSchema:
    return PaymentSchema.model_validate(await use_case.execute(input_dto=payment_id))
