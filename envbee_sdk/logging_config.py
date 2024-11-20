import logging


def setup_default_logging():
    sdk_logger = logging.getLogger("envbee_sdk")

    if not sdk_logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR)
        sdk_logger.addHandler(handler)

    sdk_logger.setLevel(logging.ERROR)
