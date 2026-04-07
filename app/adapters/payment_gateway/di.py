from dishka import Provider, Scope, provide

from app.adapters.payment_gateway.config import PaymentGatewayConfig
from app.adapters.payment_gateway.emulated import EmulatedPaymentGateway
from app.domain.interfaces.gateways.payment import IPaymentGateway


class PaymentGatewayProvider(Provider):
    def __init__(self, config: PaymentGatewayConfig) -> None:
        super().__init__()
        self._config = config

    @provide(scope=Scope.REQUEST)
    def payment_gateway(self) -> IPaymentGateway:
        return EmulatedPaymentGateway(config=self._config)
