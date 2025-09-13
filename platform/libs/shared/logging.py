import json
import logging
import os
from typing import Any, Mapping


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "extra") and isinstance(record.extra, Mapping):
            payload.update(record.extra)  # type: ignore[arg-type]
        return json.dumps(payload, default=str)


def get_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger

