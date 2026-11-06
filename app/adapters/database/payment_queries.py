from collections.abc import Mapping
from datetime import timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement

from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import (
    ClaimPaymentAttempt,
    CompletePaymentAttempt,
    GetPaymentByKey,
    NotificationStatus,
    PaymentClaim,
    PaymentStatus,
    ProcessingStatus,
    RecoverPaymentAttempt,
    SaveGatewayResult,
)
from app.domain.processing import MAX_PROCESSING_ATTEMPTS

ClaimOwner = CompletePaymentAttempt | PaymentClaim | SaveGatewayResult


def active_claim_conditions(input_dto: ClaimOwner) -> tuple[ColumnElement[bool], ...]:
    return (
        PaymentTable.id == input_dto.id,
        PaymentTable.claim_token == input_dto.token,
        PaymentTable.processing_status == ProcessingStatus.RUNNING,
        PaymentTable.deleted_at.is_(None),
    )


def live_claim_conditions(input_dto: ClaimOwner) -> tuple[ColumnElement[bool], ...]:
    return (
        *active_claim_conditions(input_dto),
        PaymentTable.lease_until > func.clock_timestamp(),
    )


def recovery_conditions(
    input_dto: CompletePaymentAttempt,
) -> tuple[ColumnElement[bool], ...]:
    return (
        *active_claim_conditions(input_dto),
        PaymentTable.lease_until <= func.clock_timestamp(),
    )


def key_conditions(input_dto: GetPaymentByKey) -> tuple[ColumnElement[bool], ...]:
    return (
        PaymentTable.idempotency_key == input_dto.key,
        PaymentTable.deleted_at.is_(None),
    )


def claim_conditions(input_dto: ClaimPaymentAttempt) -> tuple[ColumnElement[bool], ...]:
    return (
        PaymentTable.id == input_dto.id,
        PaymentTable.deleted_at.is_(None),
        PaymentTable.processing_status.in_(
            [ProcessingStatus.READY, ProcessingStatus.RETRYING]
        ),
        PaymentTable.processing_attempts == input_dto.number - 1,
        PaymentTable.processing_attempts < MAX_PROCESSING_ATTEMPTS,
    )


def gateway_result_conditions(
    input_dto: SaveGatewayResult,
) -> tuple[ColumnElement[bool], ...]:
    return (
        *live_claim_conditions(input_dto),
        PaymentTable.status == PaymentStatus.PENDING,
    )


def webhook_start_conditions(
    input_dto: PaymentClaim,
) -> tuple[ColumnElement[bool], ...]:
    return (
        *live_claim_conditions(input_dto),
        PaymentTable.status.in_([PaymentStatus.SUCCEEDED, PaymentStatus.FAILED]),
        PaymentTable.notification_status.not_in(
            [NotificationStatus.SENDING, NotificationStatus.DELIVERED]
        ),
    )


def expired_attempt_conditions(
    input_dto: RecoverPaymentAttempt,
) -> tuple[ColumnElement[bool], ...]:
    return (
        PaymentTable.deleted_at.is_(None),
        PaymentTable.processing_status == ProcessingStatus.RUNNING,
        PaymentTable.lease_until <= input_dto.now,
    )


def completion_values(input_dto: CompletePaymentAttempt) -> Mapping[str, Any]:
    return {
        "processing_status": input_dto.processing_status,
        "notification_status": input_dto.notification_status,
        "delivered_at": input_dto.delivered_at,
        "last_error": input_dto.last_error,
        "claim_token": None,
        "lease_until": None,
    }


def claim_values(input_dto: ClaimPaymentAttempt) -> Mapping[str, Any]:
    return {
        "processing_status": ProcessingStatus.RUNNING,
        "processing_attempts": PaymentTable.processing_attempts + 1,
        "claim_token": input_dto.token,
        "lease_until": func.clock_timestamp()
        + timedelta(seconds=input_dto.lease_seconds),
    }
