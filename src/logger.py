"""
Structured JSON-Lines Logger module.
Emits timestamped, machine-readable structured events to output/scraper.log.jsonl
and formatted human-readable output to standard console.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any


class StructuredLogger:
    """Writes structured JSONL log entries for observability and auditing."""

    def __init__(self, log_path: str = "output/scraper.log.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, level: str, event: str, **kwargs: Any):
        """Record a structured log event."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "event": event,
            **kwargs,
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def info(self, event: str, **kwargs: Any):
        self.log("INFO", event, **kwargs)

    def warn(self, event: str, **kwargs: Any):
        self.log("WARN", event, **kwargs)

    def error(self, event: str, **kwargs: Any):
        self.log("ERROR", event, **kwargs)

    def debug(self, event: str, **kwargs: Any):
        self.log("DEBUG", event, **kwargs)
