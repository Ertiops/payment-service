from app.domain.entities.payment import NotificationStatus, PaymentNotification


def initial_notification() -> PaymentNotification:
    return PaymentNotification(
        status=NotificationStatus.NOT_SENT,
        webhook_attempts=0,
        delivered_at=None,
        last_error=None,
    )
