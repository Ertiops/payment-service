from dataclasses import dataclass, field
from os import environ


@dataclass(frozen=True, kw_only=True, slots=True)
class RabbitMQConfig:
    dsn: str = field(default_factory=lambda: environ["APP_RABBITMQ_DSN"])
