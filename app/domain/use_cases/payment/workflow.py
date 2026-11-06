import json
from uuid import UUID

from app.domain.entities.outbox import CreateOutbox, OutboxEventType
from app.domain.entities.payment import (
    AcceptedPayment,
    CompletePaymentAttempt,
    CreatePayment,
    NotificationStatus,
    Payment,
    PaymentStatus,
    ProcessingStatus,
)
from app.domain.processing import MAX_PROCESSING_ATTEMPTS


def same_creation_request(payment: Payment, request: CreatePayment) -> bool:
    return (
        payment.amount == request.amount
        and payment.currency == request.currency
        and payment.description == request.description
        and payment.webhook_url == request.webhook_url
        and json.dumps(dict(payment.meta_data), sort_keys=True, allow_nan=False)
        == json.dumps(dict(request.meta_data), sort_keys=True, allow_nan=False)
    )


def original_accepted_response(payment: Payment) -> AcceptedPayment:
    return AcceptedPayment(
        payment_id=payment.id,
        status=PaymentStatus.PENDING,
        created_at=payment.created_at,
    )


def processing_message(payment_id: UUID, number: int) -> CreateOutbox:
    if number == 1:
        event_type = OutboxEventType.PAYMENT_CREATED
    elif number == 2:
        event_type = OutboxEventType.PAYMENT_RETRY_1
    elif number == 3:
        event_type = OutboxEventType.PAYMENT_RETRY_2
    else:
        event_type = OutboxEventType.PAYMENT_DEAD_LETTER
    return CreateOutbox(
        event_type=event_type,
        payload={
            "payment_id": str(payment_id),
            "attempt": min(number, MAX_PROCESSING_ATTEMPTS),
        },
    )


def failed_attempt(payment: Payment, token: UUID, error: str) -> CompletePaymentAttempt:
    exhausted = payment.processing_attempts >= MAX_PROCESSING_ATTEMPTS
    notification_status = NotificationStatus.NOT_SENT
    if payment.notification.webhook_attempts:
        notification_status = (
            NotificationStatus.FAILED if exhausted else NotificationStatus.RETRYING
        )
    return CompletePaymentAttempt(
        id=payment.id,
        token=token,
        processing_status=(
            ProcessingStatus.EXHAUSTED if exhausted else ProcessingStatus.RETRYING
        ),
        notification_status=notification_status,
        delivered_at=None,
        last_error=error[:2000],
    )
