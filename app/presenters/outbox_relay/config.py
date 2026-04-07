from dataclasses import dataclass, field
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
    max_attempts: int = field(
        default_factory=lambda: int(environ.get("APP_OUTBOX_MAX_ATTEMPTS", "3"))
    )
