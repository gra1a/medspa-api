"""Application logging configuration."""

import contextvars
import logging
import sys
from typing import Optional

# Set by RequestIDMiddleware so all logs during a request can include the ID.
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIDFilter(logging.Filter):
    """Inject request_id from context into each log record so the formatter can use it."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger for the application."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s %(message)s",
        stream=sys.stdout,
    )
    for handler in logging.root.handlers:
        handler.addFilter(RequestIDFilter())


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
