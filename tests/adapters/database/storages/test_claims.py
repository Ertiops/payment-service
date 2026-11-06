from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from uuid6 import uuid7

from app.adapters.database.storages.payment import PaymentStorage
from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import (
    ClaimPaymentAttempt,
    CompletePaymentAttempt,
    CreatePayment,
    GetPaymentByKey,
    NotificationStatus,
    PaymentClaim,
    PaymentStatus,
    ProcessingStatus,
    RecoverPaymentAttempt,
    SaveGatewayResult,
)
from tests.utils.payment import payment_after_gateway


async def test_create_if_absent_returns_none_for_reserved_key(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(idempotency_key="reserved")
    assert (
        await payment_storage.create_if_absent(
            input_dto=CreatePayment(
                amount=Decimal("1.00"),
                currency="USD",
                description="different",
                meta_data={},
                idempotency_key=row.idempotency_key,
                webhook_url="https://example.invalid/webhook",
            )
        )
        is None
    )


async def test_get_by_key_returns_the_matching_payment(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(idempotency_key="lookup")
    result = await payment_storage.get_by_key(input_dto=GetPaymentByKey(key="lookup"))
    assert (
        result.id,
        result.idempotency_key,
        result.processing_attempts,
        result.notification.webhook_attempts,
    ) == (row.id, "lookup", 0, 0)


async def test_claim_reserves_one_processing_attempt(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(status=PaymentStatus.PENDING)
    result = await payment_storage.claim_attempt(
        input_dto=ClaimPaymentAttempt(
            id=row.id,
            number=1,
            token=uuid7(),
            lease_seconds=30,
        )
    )
    assert (
        result.id,
        result.processing_status,
        result.processing_attempts,
        result.notification.webhook_attempts,
    ) == (row.id, "running", 1, 0)


async def test_future_envelope_cannot_skip_an_attempt(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment()
    assert (
        await payment_storage.claim_attempt(
            input_dto=ClaimPaymentAttempt(
                id=row.id,
                number=2,
                token=uuid7(),
                lease_seconds=30,
            )
        )
        is None
    )


async def test_gateway_result_requires_current_claim(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(
        status=PaymentStatus.PENDING,
        processing_status="running",
        processing_attempts=1,
        claim_token=uuid7(),
        lease_until=datetime.now(tz=UTC) + timedelta(seconds=30),
    )
    assert (
        await payment_storage.save_gateway_result(
            input_dto=SaveGatewayResult(
                id=row.id,
                token=uuid7(),
                status=PaymentStatus.SUCCEEDED,
                processed_at=datetime.now(tz=UTC),
            )
        )
        is None
    )


async def test_gateway_result_preserves_creation_data(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    token = uuid7()
    row = await create_payment(
        status=PaymentStatus.PENDING,
        processed_at=None,
        processing_status="running",
        processing_attempts=1,
        claim_token=token,
        lease_until=datetime.now(tz=UTC) + timedelta(seconds=30),
    )
    processed_at = datetime.now(tz=UTC)
    expected = payment_after_gateway(
        row,
        status=PaymentStatus.SUCCEEDED,
        processed_at=processed_at,
    )
    result = await payment_storage.save_gateway_result(
        input_dto=SaveGatewayResult(
            id=row.id,
            token=token,
            status=PaymentStatus.SUCCEEDED,
            processed_at=processed_at,
        )
    )
    assert result == expected


@pytest.mark.parametrize("status", [PaymentStatus.SUCCEEDED, PaymentStatus.FAILED])
async def test_gateway_result_cannot_replace_a_terminal_result(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
    status: PaymentStatus,
) -> None:
    token = uuid7()
    row = await create_payment(
        status=status,
        processing_status="running",
        processing_attempts=1,
        claim_token=token,
        lease_until=datetime.now(tz=UTC) + timedelta(seconds=30),
    )
    replacement = (
        PaymentStatus.FAILED
        if status == PaymentStatus.SUCCEEDED
        else PaymentStatus.SUCCEEDED
    )
    assert (
        await payment_storage.save_gateway_result(
            input_dto=SaveGatewayResult(
                id=row.id,
                token=token,
                status=replacement,
                processed_at=datetime.now(tz=UTC),
            )
        )
        is None
    )


async def test_gateway_result_for_missing_payment_is_a_noop(
    payment_storage: PaymentStorage,
) -> None:
    assert (
        await payment_storage.save_gateway_result(
            input_dto=SaveGatewayResult(
                id=uuid7(),
                token=uuid7(),
                status=PaymentStatus.SUCCEEDED,
                processed_at=datetime.now(tz=UTC),
            )
        )
        is None
    )


async def test_start_webhook_counts_only_a_delivery_start(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    token = uuid7()
    row = await create_payment(
        status=PaymentStatus.SUCCEEDED,
        processing_status="running",
        processing_attempts=2,
        claim_token=token,
        lease_until=datetime.now(tz=UTC) + timedelta(seconds=30),
    )
    result = await payment_storage.start_webhook(
        input_dto=PaymentClaim(
            id=row.id,
            token=token,
        )
    )
    assert (
        result.processing_attempts,
        result.notification.webhook_attempts,
        result.notification.status,
    ) == (2, 1, "sending")


async def test_complete_attempt_requires_current_token(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    row = await create_payment(
        processing_status="running",
        processing_attempts=1,
        claim_token=uuid7(),
        lease_until=datetime.now(tz=UTC) + timedelta(seconds=30),
    )
    assert (
        await payment_storage.complete_attempt(
            input_dto=CompletePaymentAttempt(
                id=row.id,
                token=uuid7(),
                processing_status=ProcessingStatus.RETRYING,
                notification_status=NotificationStatus.NOT_SENT,
                delivered_at=None,
                last_error="unknown",
            )
        )
        is None
    )


async def test_expired_claim_lookup_preserves_spent_count(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    token = uuid7()
    row = await create_payment(
        processing_status="running",
        processing_attempts=1,
        claim_token=token,
        lease_until=datetime.now(tz=UTC) - timedelta(seconds=1),
    )
    result = await payment_storage.get_expired_attempt(
        input_dto=RecoverPaymentAttempt(now=datetime.now(tz=UTC)),
    )
    assert (result.token, result.payment.id, result.payment.processing_attempts) == (
        token,
        row.id,
        1,
    )


async def test_recovery_fences_a_claim_without_incrementing_it(
    payment_storage: PaymentStorage,
    create_payment: Callable[..., Awaitable[PaymentTable]],
) -> None:
    token = uuid7()
    row = await create_payment(
        processing_status="running",
        processing_attempts=1,
        claim_token=token,
        lease_until=datetime.now(tz=UTC) - timedelta(seconds=1),
    )
    result = await payment_storage.recover_attempt(
        input_dto=CompletePaymentAttempt(
            id=row.id,
            token=token,
            processing_status=ProcessingStatus.RETRYING,
            notification_status=NotificationStatus.NOT_SENT,
            delivered_at=None,
            last_error="expired",
        )
    )
    assert (
        result.id,
        result.processing_status,
        result.processing_attempts,
        result.notification.status,
    ) == (row.id, "retrying", 1, "not_sent")
