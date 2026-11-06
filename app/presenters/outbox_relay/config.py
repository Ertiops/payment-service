from dataclasses import dataclass, field
from math import isfinite
from os import environ

from app.adapters.database.config import DatabaseConfig
from app.adapters.rabbitmq.config import RabbitMQConfig
from app.application.config import AppConfig


@dataclass(frozen=True, kw_only=True, slots=True)
class OutboxRelayConfig:
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    rabbitmq: RabbitMQConfig = field(default_factory=RabbitMQConfig)
    poll_interval: float = field(
        default_factory=lambda: float(environ.get("APP_OUTBOX_POLL_INTERVAL", "1"))
    )
    initial_delay_seconds: float = field(
        default_factory=lambda: float(
            environ.get("APP_OUTBOX_INITIAL_DELAY_SECONDS", "1")
        )
    )
    max_delay_seconds: float = field(
        default_factory=lambda: float(environ.get("APP_OUTBOX_MAX_DELAY_SECONDS", "30"))
    )

    def __post_init__(self) -> None:
        if not all(
            isfinite(value)
            for value in (
                self.poll_interval,
                self.initial_delay_seconds,
                self.max_delay_seconds,
            )
        ):
            raise ValueError("Outbox timing values must be finite")
        if self.poll_interval <= 0 or self.initial_delay_seconds <= 0:
            raise ValueError("Outbox polling and retry delay must be positive")
        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError("Outbox maximum delay must be at least the initial delay")
