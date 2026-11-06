from dataclasses import dataclass, field

from app.adapters.database.config import DatabaseConfig
from app.adapters.payment_gateway.config import PaymentGatewayConfig
from app.adapters.rabbitmq.config import RabbitMQConfig
from app.adapters.webhook.config import WebhookConfig
from app.application.config import AppConfig
from app.domain.processing import ProcessingConfig


@dataclass(frozen=True, kw_only=True, slots=True)
class PaymentConsumerConfig:
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    rabbitmq: RabbitMQConfig = field(default_factory=RabbitMQConfig)
    payment_gateway: PaymentGatewayConfig = field(default_factory=PaymentGatewayConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)

    def __post_init__(self) -> None:
        if self.processing.lease_seconds <= (
            self.processing.gateway_timeout_seconds + self.webhook.timeout_seconds
        ):
            raise ValueError("Attempt lease must exceed the combined external timeouts")
