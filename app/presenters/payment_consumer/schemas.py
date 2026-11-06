import logging
from uuid import UUID

from faststream.exceptions import RejectMessage
from faststream.rabbit.message import RabbitMessage
from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger(__name__)


class PaymentMessageSchema(BaseModel):
    payment_id: UUID
    attempt: int = Field(default=1, ge=1, le=3, strict=True)


async def decode_payment_message(message: RabbitMessage) -> PaymentMessageSchema:
    try:
        return PaymentMessageSchema.model_validate_json(message.body)
    except ValidationError as exc:
        log.warning("Rejecting malformed payment envelope")
        raise RejectMessage() from exc
