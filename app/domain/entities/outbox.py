from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from typing import Any
from uuid import UUID


@unique
class OutboxEventType(StrEnum):
    PAYMENT_CREATED = "payments.new"


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
