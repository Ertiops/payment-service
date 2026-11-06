from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique
from typing import Any
from uuid import UUID

from app.application.entities import UNSET, Unset
from app.domain.entities.common import ToDictMixin


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


@unique
class ProcessingStatus(StrEnum):
    READY = "ready"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    EXHAUSTED = "exhausted"


@unique
class NotificationStatus(StrEnum):
    NOT_SENT = "not_sent"
    SENDING = "sending"
    RETRYING = "retrying"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, kw_only=True, slots=True)
class PaymentNotification:
    status: NotificationStatus
    webhook_attempts: int
    delivered_at: datetime | None
    last_error: str | None


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
    processing_status: ProcessingStatus
    processing_attempts: int
    notification: PaymentNotification


@dataclass(frozen=True, kw_only=True, slots=True)
class CreatePayment:
    amount: Decimal
    currency: PaymentCurrency
    description: str
    meta_data: Mapping[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str


@dataclass(frozen=True, kw_only=True, slots=True)
class AcceptedPayment:
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class UpdatePayment(ToDictMixin):
    id: UUID
    amount: Decimal | Unset = UNSET
    currency: PaymentCurrency | Unset = UNSET
    description: str | Unset = UNSET
    meta_data: Mapping[str, Any] | Unset = UNSET
    status: PaymentStatus | Unset = UNSET
    idempotency_key: str | Unset = UNSET
    webhook_url: str | Unset = UNSET
    processed_at: datetime | Unset = UNSET


@dataclass(frozen=True, kw_only=True, slots=True)
class ProcessPayment:
    id: UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class PaymentAttempt:
    id: UUID
    number: int


@dataclass(frozen=True, kw_only=True, slots=True)
class GetPaymentByKey:
    key: str


@dataclass(frozen=True, kw_only=True, slots=True)
class ClaimPaymentAttempt:
    id: UUID
    number: int
    token: UUID
    lease_seconds: float


@dataclass(frozen=True, kw_only=True, slots=True)
class PaymentClaim:
    id: UUID
    token: UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class SaveGatewayResult:
    id: UUID
    token: UUID
    status: PaymentStatus
    processed_at: datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class CompletePaymentAttempt:
    id: UUID
    token: UUID
    processing_status: ProcessingStatus
    notification_status: NotificationStatus
    delivered_at: datetime | None
    last_error: str | None


@dataclass(frozen=True, kw_only=True, slots=True)
class ExpiredPaymentAttempt:
    payment: Payment
    token: UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class RecoverPaymentAttempt:
    now: datetime
