from __future__ import annotations

import logging.config
from pathlib import Path


LOG_DIR = Path("..") / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "ingestion.log"
BACKUP_COUNT = 5


def setup_logging(level: str = "INFO") -> None:
    """
    Configure application logging.
    """

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s | "
                        "%(levelname)-8s | "
                        "%(name)s | "
                        "%(message)s"
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": LOG_FILE,
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": BACKUP_COUNT,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": [
                    "console",
                    "file",
                ],
                "level": level,
            },
        }
    )