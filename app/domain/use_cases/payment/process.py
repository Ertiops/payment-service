import asyncio
import logging
from datetime import UTC, datetime

from uuid6 import uuid7

from app.application.exceptions import PaymentProcessingException
from app.application.use_case import IUseCase
from app.domain.entities.payment import (
    ClaimPaymentAttempt,
    CompletePaymentAttempt,
    NotificationStatus,
    Payment,
    PaymentAttempt,
    PaymentClaim,
    PaymentStatus,
    ProcessingStatus,
    ProcessPayment,
    SaveGatewayResult,
)
from app.domain.entities.webhook import SendPaymentWebhook
from app.domain.interfaces.gateways.payment import IPaymentGateway
from app.domain.interfaces.storages.outbox import IOutboxStorage
from app.domain.interfaces.storages.payment import IPaymentStorage
from app.domain.interfaces.webhooks.payment import IPaymentWebhookSender
from app.domain.processing import MAX_PROCESSING_ATTEMPTS, ProcessingConfig
from app.domain.uow import AbstractUow
from app.domain.use_cases.payment.workflow import failed_attempt, processing_message

log = logging.getLogger(__name__)


def create_payment_webhook(input_dto: Payment) -> SendPaymentWebhook:
    if input_dto.processed_at is None:
        raise PaymentProcessingException("Processed payment has no processed_at")
    return SendPaymentWebhook(
        payment_id=input_dto.id,
        status=input_dto.status,
        processed_at=input_dto.processed_at,
        webhook_url=input_dto.webhook_url,
    )


class ProcessPaymentUC(IUseCase[PaymentAttempt, Payment | None]):
    def __init__(
        self,
        uow: AbstractUow,
        payment_storage: IPaymentStorage,
        outbox_storage: IOutboxStorage,
        payment_gateway: IPaymentGateway,
        payment_webhook_sender: IPaymentWebhookSender,
        config: ProcessingConfig,
    ) -> None:
        self._uow = uow
        self._payment_storage = payment_storage
        self._outbox_storage = outbox_storage
        self._payment_gateway = payment_gateway
        self._payment_webhook_sender = payment_webhook_sender
        self._config = config

    async def execute(self, *, input_dto: PaymentAttempt) -> Payment | None:
        if not 1 <= input_dto.number <= MAX_PROCESSING_ATTEMPTS:
            return None
        token = uuid7()
        async with self._uow:
            payment = await self._payment_storage.claim_attempt(
                input_dto=ClaimPaymentAttempt(
                    id=input_dto.id,
                    number=input_dto.number,
                    token=token,
                    lease_seconds=self._config.lease_seconds,
                )
            )
        if payment is None:
            return None
        try:
            if payment.status == PaymentStatus.PENDING:
                async with asyncio.timeout(self._config.gateway_timeout_seconds):
                    status = await self._payment_gateway.process(
                        input_dto=ProcessPayment(id=payment.id)
                    )
                if status not in (PaymentStatus.SUCCEEDED, PaymentStatus.FAILED):
                    raise PaymentProcessingException("Gateway returned no final result")
                async with self._uow:
                    updated_payment = await self._payment_storage.save_gateway_result(
                        input_dto=SaveGatewayResult(
                            id=payment.id,
                            token=token,
                            status=status,
                            processed_at=datetime.now(tz=UTC),
                        )
                    )
                if updated_payment is None:
                    return None
                payment = updated_payment
            async with self._uow:
                updated_payment = await self._payment_storage.start_webhook(
                    input_dto=PaymentClaim(id=payment.id, token=token)
                )
            if updated_payment is None:
                return None
            payment = updated_payment
            await self._payment_webhook_sender.send(
                input_dto=create_payment_webhook(input_dto=payment)
            )
        except Exception as exc:
            log.exception("Payment attempt failed for %s", payment.id)
            async with self._uow:
                payment = await self._payment_storage.complete_attempt(
                    input_dto=failed_attempt(payment, token, type(exc).__name__)
                )
                if payment is not None:
                    await self._outbox_storage.create(
                        input_dto=processing_message(
                            payment.id, payment.processing_attempts + 1
                        )
                    )
            return payment
        async with self._uow:
            return await self._payment_storage.complete_attempt(
                input_dto=CompletePaymentAttempt(
                    id=payment.id,
                    token=token,
                    processing_status=ProcessingStatus.COMPLETED,
                    notification_status=NotificationStatus.DELIVERED,
                    delivered_at=datetime.now(tz=UTC),
                    last_error=None,
                )
            )
