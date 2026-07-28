from __future__ import annotations

import logging
import re
from pathlib import Path


SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(password|encodePassword|csrftoken|cookie|authorization)\s*[:=]\s*([^\s,;]+)"),
]


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in SENSITIVE_PATTERNS:
            message = pattern.sub(r"\1=***", message)
        record.msg = message
        record.args = ()
        return True


def make_logger(name: str, path: Path, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(f"{name}-{path}")
    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    return logger
