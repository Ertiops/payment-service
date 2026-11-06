import argparse
import logging

from aiomisc import Service, entrypoint
from aiomisc_log import LogFormat, LogLevel, basic_config

from app.presenters.outbox_relay.config import OutboxRelayConfig
from app.presenters.outbox_relay.service import OutboxRelayService
from app.presenters.payment_consumer.config import PaymentConsumerConfig
from app.presenters.payment_consumer.service import PaymentConsumerService
from app.presenters.rest.config import RestConfig
from app.presenters.rest.service import RestService

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("api", "worker"))
    role = parser.parse_args().role
    basic_config(level=LogLevel.info, log_format=LogFormat.color)

    services: list[Service]
    if role == "api":
        rest_config = RestConfig()
        services = [
            RestService(
                host=rest_config.host,
                port=rest_config.port,
                config=rest_config,
            )
        ]
        debug = rest_config.app.debug
    else:
        consumer_config = PaymentConsumerConfig()
        services = [
            OutboxRelayService(config=OutboxRelayConfig()),
            PaymentConsumerService(config=consumer_config),
        ]
        debug = consumer_config.app.debug
    with entrypoint(*services, pool_size=4, debug=debug) as loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
