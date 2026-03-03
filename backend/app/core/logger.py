"""
app/core/logger.py
------------------
Structured JSON logging for SR Agro Vision backend.

Usage anywhere in the project:
    from app.core.logger import get_logger
    logger = get_logger(__name__)

    logger.info("Image uploaded", extra={"user_id": user.id, "image_id": image.id})
    logger.error("Processing failed", extra={"task_id": task.id}, exc_info=True)
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Every record includes:
        timestamp  — ISO-8601 UTC
        level      — DEBUG / INFO / WARNING / ERROR / CRITICAL
        logger     — logger name (usually the module that created it)
        message    — the log message
        module     — Python module filename (without .py)
        function   — function name where the log was emitted

    If extra fields are passed to the logger call they are merged
    into the top-level JSON object:
        logger.info("upload", extra={"user_id": "abc", "image_id": "xyz"})

    If exc_info=True is passed, an "exception" key is added.
    """

    # Keys injected by logging internals that we don't want in the output
    _LOGGING_INTERNALS = frozenset(
        logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
    )

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        # Merge any extra fields passed via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in self._LOGGING_INTERNALS and not key.startswith("_"):
                log_data[key] = value

        # Append formatted exception if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str, ensure_ascii=False)


def _build_logger(name: str, level: int) -> logging.Logger:
    """Internal factory — creates and configures a named logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        # Already configured (e.g. imported twice); avoid duplicate handlers
        return logger

    formatter = JSONFormatter()

    # --- stdout handler (always active: dev, Docker, systemd) ---
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # --- file handler (skipped if LOG_FILE_DIR is explicitly empty) ---
    log_dir_env = os.getenv("LOG_FILE_DIR", "logs")
    if log_dir_env:
        log_dir = Path(log_dir_env)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "sr_agro.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to the root logger (avoids duplicate output)
    logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# Resolve the global log level once at import time.
# Override with LOG_LEVEL env var: DEBUG | INFO | WARNING | ERROR | CRITICAL
# ---------------------------------------------------------------------------
_LOG_LEVEL: int = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Return a structured JSON logger for the given module name.

    Typical usage:
        from app.core.logger import get_logger
        logger = get_logger(__name__)
    """
    return _build_logger(name, _LOG_LEVEL)
