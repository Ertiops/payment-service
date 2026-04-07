from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.payment import PaymentStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class SendPaymentWebhook:
    payment_id: UUID
    status: PaymentStatus
    processed_at: datetime
    webhook_url: str
