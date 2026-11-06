import logging
from types import MappingProxyType

from aiohttp import ClientResponse
from asyncly import ResponseHandlersType

from app.application.exceptions import WebhookDeliveryException

log = logging.getLogger(__name__)


async def handle_success(response: ClientResponse) -> None:
    return None


async def raise_webhook_delivery_exception(response: ClientResponse) -> None:
    log.warning("WEBHOOK_DELIVERY_FAILED: %s", response.status)
    raise WebhookDeliveryException("Webhook delivery failed")


PAYMENT_WEBHOOK_HANDLERS: ResponseHandlersType = MappingProxyType(
    {
        "2xx": handle_success,
        "*": raise_webhook_delivery_exception,
    }
)
