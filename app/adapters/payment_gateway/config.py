from dataclasses import dataclass, field
from os import environ


@dataclass(frozen=True, kw_only=True, slots=True)
class PaymentGatewayConfig:
    min_delay_seconds: float = field(
        default_factory=lambda: float(
            environ.get("APP_PAYMENT_GATEWAY_MIN_DELAY_SECONDS", "2")
        )
    )
    max_delay_seconds: float = field(
        default_factory=lambda: float(
            environ.get("APP_PAYMENT_GATEWAY_MAX_DELAY_SECONDS", "5")
        )
    )
    success_rate: float = field(
        default_factory=lambda: float(
            environ.get("APP_PAYMENT_GATEWAY_SUCCESS_RATE", "0.9")
        )
    )
