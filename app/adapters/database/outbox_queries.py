from collections.abc import Mapping
from typing import Any

from sqlalchemy.sql.elements import ColumnElement

from app.adapters.database.tables import OutboxTable
from app.domain.entities.outbox import (
    GetOutboxToPublish,
    OutboxStatus,
    RescheduleOutbox,
)


def publication_due_conditions(
    input_dto: GetOutboxToPublish,
) -> tuple[ColumnElement[bool], ...]:
    return (
        OutboxTable.status == OutboxStatus.PENDING,
        OutboxTable.available_at <= input_dto.now,
        OutboxTable.deleted_at.is_(None),
    )


def publication_retry_values(input_dto: RescheduleOutbox) -> Mapping[str, Any]:
    return {
        "status": OutboxStatus.PENDING,
        "attempts": input_dto.attempts,
        "last_error": input_dto.last_error,
        "available_at": input_dto.available_at,
    }
