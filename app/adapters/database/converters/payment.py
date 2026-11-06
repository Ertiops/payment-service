from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import (
    NotificationStatus,
    Payment,
    PaymentNotification,
    ProcessingStatus,
)


def convert_payment_table_to_dto(
    *,
    result: PaymentTable,
) -> Payment:
    return Payment(
        id=result.id,
        amount=result.amount,
        currency=result.currency,
        description=result.description,
        meta_data=result.meta_data,
        status=result.status,
        idempotency_key=result.idempotency_key,
        webhook_url=result.webhook_url,
        processed_at=result.processed_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
        processing_status=ProcessingStatus(result.processing_status),
        processing_attempts=result.processing_attempts,
        notification=PaymentNotification(
            status=NotificationStatus(result.notification_status),
            webhook_attempts=result.webhook_attempts,
            delivered_at=result.delivered_at,
            last_error=result.last_error if result.webhook_attempts else None,
        ),
    )
