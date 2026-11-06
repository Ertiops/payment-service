import json
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, Field, field_validator

from app.domain.entities.payment import (
    NotificationStatus,
    PaymentCurrency,
    PaymentStatus,
    ProcessingStatus,
)
from app.presenters.rest.schemas import BaseSchema


class PaymentNotificationSchema(BaseSchema):
    status: NotificationStatus
    webhook_attempts: int
    delivered_at: datetime | None
    last_error: str | None


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
    processing_status: ProcessingStatus
    processing_attempts: int
    notification: PaymentNotificationSchema


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

    @field_validator("meta_data")
    @classmethod
    def validate_json(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        json.dumps(dict(value), allow_nan=False)
        return value
