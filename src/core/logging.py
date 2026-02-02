import logging
import os


def setup_logging(level: int | None = None) -> None:
    if level is None:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = {
            "CRITICAL": logging.CRITICAL,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
        }.get(level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
