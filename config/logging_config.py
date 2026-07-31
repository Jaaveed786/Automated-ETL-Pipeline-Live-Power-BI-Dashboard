import logging
import logging.config
import os
from pathlib import Path


def configure_logging(log_level: str = None, log_to_file: bool = False) -> None:
    """
    Configures structured logging for the entire pipeline.

    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR).
                   Defaults to LOG_LEVEL env var, then INFO.
        log_to_file: If True, also writes logs to logs/pipeline.log
    """
    level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
            "level": level,
        }
    }

    if log_to_file:
        Path("logs").mkdir(exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/pipeline.log",
            "maxBytes": 5_000_000,   # 5 MB
            "backupCount": 3,
            "formatter": "standard",
            "level": level,
        }

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": handlers,
        "root": {
            "level": level,
            "handlers": list(handlers.keys()),
        },
    }

    logging.config.dictConfig(config)
