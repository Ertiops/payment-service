from decimal import Decimal

from app.domain.entities.payment import (
    CreatePayment,
    NotificationStatus,
    PaymentCurrency,
    PaymentNotification,
    PaymentStatus,
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
        status=PaymentStatus.PENDING,
        idempotency_key=key,
        webhook_url="https://example.invalid/webhook",
    )
