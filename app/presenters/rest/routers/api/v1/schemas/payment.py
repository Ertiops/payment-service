from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, Field

from app.domain.entities.payment import PaymentCurrency, PaymentStatus
from app.presenters.rest.schemas import BaseSchema


class PaymentSchema(BaseSchema):
    id: UUID
    amount: Decimal
    currency: PaymentCurrency
    description: str
    meta_data: Mapping[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaymentAcceptedSchema(BaseSchema):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class CreatePaymentSchema(BaseSchema):
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: PaymentCurrency
    description: str = Field(min_length=1, max_length=2000)
    meta_data: Mapping[str, Any]
    webhook_url: AnyHttpUrl
