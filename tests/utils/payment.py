from datetime import datetime
from decimal import Decimal

from dirty_equals import IsDatetime

from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import (
    CreatePayment,
    NotificationStatus,
    Payment,
    PaymentCurrency,
    PaymentNotification,
    PaymentStatus,
    ProcessingStatus,
)


def initial_notification() -> PaymentNotification:
    return PaymentNotification(
        status=NotificationStatus.NOT_SENT,
        webhook_attempts=0,
        delivered_at=None,
        last_error=None,
    )


def creation(key: str) -> CreatePayment:
    return CreatePayment(
        amount=Decimal("10.50"),
        currency=PaymentCurrency.USD,
        description="integration",
        meta_data={"order": "1"},
        idempotency_key=key,
        webhook_url="https://example.invalid/webhook",
    )


def payment_after_gateway(
    row: PaymentTable, *, status: PaymentStatus, processed_at: datetime
) -> Payment:
    return Payment(
        id=row.id,
        amount=row.amount,
        currency=row.currency,
        description=row.description,
        meta_data=row.meta_data,
        status=status,
        idempotency_key=row.idempotency_key,
        webhook_url=row.webhook_url,
        processed_at=processed_at,
        created_at=row.created_at,
        updated_at=IsDatetime,
        processing_status=ProcessingStatus(row.processing_status),
        processing_attempts=row.processing_attempts,
        notification=PaymentNotification(
            status=NotificationStatus(row.notification_status),
            webhook_attempts=row.webhook_attempts,
            delivered_at=row.delivered_at,
            last_error=row.last_error,
        ),
    )
