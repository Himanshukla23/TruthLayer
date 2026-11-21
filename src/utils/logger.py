"""Standardized logging utility for TruthLayer with automatic secret redaction."""

import logging
import re
import sys
from typing import Optional

# Regex patterns for detecting and redacting sensitive tokens
_SENSITIVE_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),            # Google Gemini / Google Cloud API keys
    re.compile(r"gsk_[0-9A-Za-z]{30,}"),             # Groq API keys
    re.compile(r"tvly-[0-9A-Za-z-_]{20,}"),          # Tavily API keys
    re.compile(r"Bearer\s+[A-Za-z0-9\-_\.=]+", re.I), # Bearer tokens
]


class SensitiveDataFilter(logging.Filter):
    """Logging filter that scrubs sensitive API tokens and authorization headers."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact(a) if isinstance(a, str) else a for a in record.args)
        return True

    @staticmethod
    def _redact(text: str) -> str:
        scrubbed = text
        for pattern in _SENSITIVE_PATTERNS:
            scrubbed = pattern.sub("[REDACTED_CREDENTIAL]", scrubbed)
        return scrubbed


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Return a logger instance configured with formatting and credential scrubbing.

    Args:
        name: Name of the logger (typically __name__).
        level: Optional log level string (e.g. 'DEBUG', 'INFO', 'WARNING').

    Returns:
        Configured logging.Logger.
    """
    logger = logging.getLogger(name)

    # Determine log level
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid duplicate handlers if already attached
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    # Ensure sensitive data filter is attached to logger itself
    if not any(isinstance(f, SensitiveDataFilter) for f in logger.filters):
        logger.addFilter(SensitiveDataFilter())

    return logger
