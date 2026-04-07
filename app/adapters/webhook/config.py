from dataclasses import dataclass, field
from os import environ


@dataclass(frozen=True, kw_only=True, slots=True)
class WebhookConfig:
    base_url: str = field(
        default_factory=lambda: environ.get(
            "APP_WEBHOOK_BASE_URL", "http://webhook.site"
        )
    )
    timeout_seconds: float = field(
        default_factory=lambda: float(environ.get("APP_WEBHOOK_TIMEOUT_SECONDS", "5"))
    )
    max_attempts: int = field(
        default_factory=lambda: int(environ.get("APP_WEBHOOK_MAX_ATTEMPTS", "3"))
    )
    initial_delay_seconds: float = field(
        default_factory=lambda: float(
            environ.get("APP_WEBHOOK_INITIAL_DELAY_SECONDS", "1")
        )
    )
