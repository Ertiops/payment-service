from dataclasses import dataclass, field
from math import isfinite
from os import environ


@dataclass(frozen=True, kw_only=True, slots=True)
class RabbitMQConfig:
    dsn: str = field(default_factory=lambda: environ["APP_RABBITMQ_DSN"])
    retry_delay_seconds: float = field(
        default_factory=lambda: float(
            environ.get("APP_RETRY_INITIAL_DELAY_SECONDS", "1")
        )
    )
    publish_timeout_seconds: float = field(
        default_factory=lambda: float(environ.get("APP_PUBLISH_TIMEOUT_SECONDS", "5"))
    )

    def __post_init__(self) -> None:
        if not isfinite(self.retry_delay_seconds) or self.retry_delay_seconds < 0.001:
            raise ValueError("Retry delay must be finite and at least one millisecond")
        if (
            not isfinite(self.publish_timeout_seconds)
            or self.publish_timeout_seconds <= 0
        ):
            raise ValueError("Publish timeout must be finite and positive")
