"""
Pipeline Event Notification System.
Provides a publisher-subscriber model for pipeline lifecycle events,
allowing multiple listeners (console logger, file logger, webhooks)
to react to scraping milestones, warnings, and completion events.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class EventLevel(Enum):
    """Severity level for pipeline events."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Types of pipeline lifecycle events."""
    PIPELINE_START = "pipeline_start"
    PIPELINE_END = "pipeline_end"
    STAGE_START = "stage_start"
    STAGE_END = "stage_end"
    PAGE_FETCHED = "page_fetched"
    PAGE_CACHED = "page_cached"
    PAGE_FAILED = "page_failed"
    RECORD_VALIDATED = "record_validated"
    RECORD_REJECTED = "record_rejected"
    EXPORT_COMPLETE = "export_complete"
    CACHE_HIT = "cache_hit"
    RATE_LIMITED = "rate_limited"
    CIRCUIT_BREAKER_TRIP = "circuit_breaker_trip"
    CUSTOM = "custom"


@dataclass
class PipelineEvent:
    """Represents a single pipeline lifecycle event."""
    event_type: EventType
    level: EventLevel
    message: str
    timestamp: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data,
        }


# Type alias for event handler callbacks
EventHandler = Callable[[PipelineEvent], None]


class NotificationManager:
    """
    Central hub for publishing and subscribing to pipeline events.
    Supports multiple handlers per event type and global catch-all listeners.
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._global_handlers: list[EventHandler] = []
        self._event_log: list[PipelineEvent] = []
        self._max_log_size: int = 1000

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Register a handler that receives ALL events (global listener)."""
        self._global_handlers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> bool:
        """Remove a specific handler. Returns True if found and removed."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                return True
            except ValueError:
                return False
        return False

    def emit(self, event: PipelineEvent) -> int:
        """
        Publish an event to all matching handlers.
        Returns the number of handlers that were invoked.
        """
        # Store in event log
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

        invoked = 0

        # Dispatch to type-specific handlers
        type_handlers = self._handlers.get(event.event_type, [])
        for handler in type_handlers:
            try:
                invoked += 1
                handler(event)
            except Exception:
                pass  # Handlers should not break the pipeline

        # Dispatch to global handlers
        for handler in self._global_handlers:
            try:
                invoked += 1
                handler(event)
            except Exception:
                pass

        return invoked

    def emit_simple(
        self,
        event_type: EventType,
        message: str,
        level: EventLevel = EventLevel.INFO,
        **data: Any,
    ) -> int:
        """Convenience method to emit an event with keyword data."""
        event = PipelineEvent(
            event_type=event_type,
            level=level,
            message=message,
            data=data,
        )
        return self.emit(event)

    def get_event_log(self, event_type: EventType | None = None) -> list[dict[str, Any]]:
        """Retrieve the event log, optionally filtered by event type."""
        events = self._event_log
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events]

    def get_event_counts(self) -> dict[str, int]:
        """Return counts of events by type."""
        counts: dict[str, int] = {}
        for event in self._event_log:
            key = event.event_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def clear_log(self) -> int:
        """Clear the event log. Returns the count of cleared events."""
        count = len(self._event_log)
        self._event_log.clear()
        return count

    @property
    def handler_count(self) -> int:
        """Total number of registered handlers."""
        type_count = sum(len(h) for h in self._handlers.values())
        return type_count + len(self._global_handlers)


# ----- Built-in Handler Factories -----

def create_console_handler(min_level: EventLevel = EventLevel.INFO) -> EventHandler:
    """
    Create a handler that prints events to the console.
    Only prints events at or above the specified minimum level.
    """
    level_order = {
        EventLevel.DEBUG: 0,
        EventLevel.INFO: 1,
        EventLevel.WARNING: 2,
        EventLevel.ERROR: 3,
        EventLevel.CRITICAL: 4,
    }

    def handler(event: PipelineEvent) -> None:
        if level_order.get(event.level, 0) >= level_order.get(min_level, 0):
            prefix = f"[{event.level.value}]"
            print(f"  {prefix:12s} {event.event_type.value}: {event.message}")

    return handler


def create_file_handler(log_path: str) -> EventHandler:
    """Create a handler that appends events as JSONL to a file."""

    def handler(event: PipelineEvent) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    return handler


def create_counter_handler() -> tuple[EventHandler, Callable[[], dict[str, int]]]:
    """
    Create a handler that counts events by type.
    Returns (handler, get_counts_fn).
    """
    counts: dict[str, int] = {}

    def handler(event: PipelineEvent) -> None:
        key = event.event_type.value
        counts[key] = counts.get(key, 0) + 1

    def get_counts() -> dict[str, int]:
        return dict(counts)

    return handler, get_counts
