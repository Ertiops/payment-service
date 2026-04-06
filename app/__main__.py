import logging

from aiomisc import Service, entrypoint
from aiomisc_log import LogFormat, LogLevel, basic_config

from app.presenters.rest.config import RestConfig
from app.presenters.rest.service import RestService

log = logging.getLogger(__name__)


def main() -> None:
    basic_config(level=LogLevel.info, log_format=LogFormat.color)

    rest_config = RestConfig()
    services: list[Service] = [
        RestService(
            host=rest_config.host,
            port=rest_config.port,
            config=rest_config,
        ),
    ]

    with entrypoint(
        *services,
        pool_size=4,
        debug=rest_config.app.debug,
    ) as loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
