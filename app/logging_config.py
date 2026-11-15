import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON objects for production observability (ELK, CloudWatch, Loki).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Include custom attributes if passed via extra
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "path"):
            log_record["path"] = record.path
        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("pharmacy_platform")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Also capture uvicorn access logs cleanly
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(handler)

    return logger


logger = setup_logging()
