# ------------------------------------
# Copyright (c) envbee
# Licensed under the MIT License.
# ------------------------------------

__version__ = "1.8.0"

from .logging_config import setup_default_logging
from .main import Envbee  # noqa: F401

# Global logging configuration
setup_default_logging()
