import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(correlation_id: str | None) -> None:
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        correlation_id = get_correlation_id()
        if correlation_id:
            payload["correlation_id"] = correlation_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key in ("event", "provider", "latency_ms", "status", "trace_id", "model", "tokens", "retry_count", "categories", "message_preview"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> logging.Logger:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)

    return logging.getLogger("agenticai")
