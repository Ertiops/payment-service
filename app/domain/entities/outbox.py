from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from typing import Any
from uuid import UUID


@unique
class OutboxEventType(StrEnum):
    PAYMENT_CREATED = "payments.new"
    PAYMENT_RETRY_1 = "payments.retry.1"
    PAYMENT_RETRY_2 = "payments.retry.2"
    PAYMENT_DEAD_LETTER = "payments.new.dlq"


@unique
class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass(frozen=True, kw_only=True, slots=True)
class Outbox:
    id: UUID
    event_type: OutboxEventType
    payload: Mapping[str, Any]
    status: OutboxStatus
    attempts: int
    last_error: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateOutbox:
    event_type: OutboxEventType
    payload: Mapping[str, Any]
    status: OutboxStatus
    attempts: int
    last_error: str | None
    published_at: datetime | None


@dataclass(frozen=True, kw_only=True, slots=True)
class GetOutboxToPublish:
    now: datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class MarkOutboxAsPublished:
    id: UUID
    status: OutboxStatus
    published_at: datetime
    last_error: str | None


@dataclass(frozen=True, kw_only=True, slots=True)
class MarkOutboxAsFailed:
    id: UUID
    status: OutboxStatus
    attempts: int
    last_error: str


@dataclass(frozen=True, kw_only=True, slots=True)
class PublishOutboxMessage:
    id: UUID
    event_type: OutboxEventType
    payload: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True, slots=True)
class PublishNextOutbox:
    initial_delay_seconds: float
    max_delay_seconds: float


@dataclass(frozen=True, kw_only=True, slots=True)
class RescheduleOutbox:
    id: UUID
    attempts: int
    last_error: str
    available_at: datetime
