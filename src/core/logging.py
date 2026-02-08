import logging


def setup_logging(level: int | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO if level is None else level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
