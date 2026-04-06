from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique
from typing import Any
from uuid import UUID


@unique
class PaymentCurrency(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


@unique
class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, kw_only=True, slots=True)
class Payment:
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


@dataclass(frozen=True, kw_only=True, slots=True)
class CreatePayment:
    amount: Decimal
    currency: PaymentCurrency
    description: str
    meta_data: Mapping[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
