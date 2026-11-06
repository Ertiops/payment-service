from dataclasses import dataclass, field
from math import isfinite
from os import environ

MAX_PROCESSING_ATTEMPTS = 3


@dataclass(frozen=True, kw_only=True, slots=True)
class ProcessingConfig:
    lease_seconds: float = field(
        default_factory=lambda: float(environ.get("APP_PROCESSING_LEASE_SECONDS", "30"))
    )
    gateway_timeout_seconds: float = field(
        default_factory=lambda: float(environ.get("APP_GATEWAY_TIMEOUT_SECONDS", "10"))
    )

    def __post_init__(self) -> None:
        if (
            not isfinite(self.gateway_timeout_seconds)
            or self.gateway_timeout_seconds <= 0
        ):
            raise ValueError("Gateway timeout must be positive")
        if (
            not isfinite(self.lease_seconds)
            or self.lease_seconds <= self.gateway_timeout_seconds
        ):
            raise ValueError("Attempt lease must exceed gateway timeout")
