from __future__ import annotations

import logging.config
from pathlib import Path

DEFAULT_LOG_DIR = Path("logs")
LOG_FILE_NAME = "ingestion.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def setup_logging(
    level: str = "INFO",
    log_dir: Path | str = DEFAULT_LOG_DIR,
) -> None:
    """Configure application logging.

    Attaches to the root logger a console handler and a rotating file handler
    writing to log_dir/ingestion.log, keeping up to BACKUP_COUNT rotated files.
    The log directory is created if missing, parents included.

    Args:
        level: Minimum level logged by the root logger.
        log_dir: Directory the log files are written to. Relative paths are
            resolved against the current working directory.
    """

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / LOG_FILE_NAME

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
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
                    "filename": log_file,
                    "maxBytes": MAX_BYTES,
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
