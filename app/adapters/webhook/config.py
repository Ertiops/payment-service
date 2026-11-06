from dataclasses import dataclass, field
from math import isfinite
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

    def __post_init__(self) -> None:
        if not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("Webhook timeout must be finite and positive")
