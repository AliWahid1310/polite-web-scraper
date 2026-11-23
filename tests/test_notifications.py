"""Tests for the pipeline notification system (src/notifications.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.notifications import (
    EventLevel,
    EventType,
    NotificationManager,
    PipelineEvent,
    create_console_handler,
    create_counter_handler,
    create_file_handler,
)


class TestPipelineEvent:
    """Test PipelineEvent data class."""

    def test_event_creation(self):
        event = PipelineEvent(
            event_type=EventType.PIPELINE_START,
            level=EventLevel.INFO,
            message="Pipeline started",
        )
        assert event.event_type == EventType.PIPELINE_START
        assert event.level == EventLevel.INFO
        assert event.message == "Pipeline started"
        assert event.timestamp  # auto-populated

    def test_event_to_dict(self):
        event = PipelineEvent(
            event_type=EventType.PAGE_FETCHED,
            level=EventLevel.DEBUG,
            message="Fetched page",
            data={"url": "https://example.com"},
        )
        d = event.to_dict()
        assert d["event_type"] == "page_fetched"
        assert d["level"] == "DEBUG"
        assert d["data"]["url"] == "https://example.com"

    def test_event_custom_timestamp(self):
        event = PipelineEvent(
            event_type=EventType.CUSTOM,
            level=EventLevel.WARNING,
            message="Test",
            timestamp="2026-01-01T00:00:00+00:00",
        )
        assert event.timestamp == "2026-01-01T00:00:00+00:00"


class TestNotificationManager:
    """Test the central notification manager."""

    def test_subscribe_and_emit(self):
        manager = NotificationManager()
        received = []

        def handler(event: PipelineEvent):
            received.append(event)

        manager.subscribe(EventType.PIPELINE_START, handler)
        count = manager.emit_simple(EventType.PIPELINE_START, "Started")
        assert count == 1
        assert len(received) == 1
        assert received[0].message == "Started"

    def test_multiple_handlers(self):
        manager = NotificationManager()
        results = {"a": 0, "b": 0}

        def handler_a(event: PipelineEvent):
            results["a"] += 1

        def handler_b(event: PipelineEvent):
            results["b"] += 1

        manager.subscribe(EventType.PAGE_FETCHED, handler_a)
        manager.subscribe(EventType.PAGE_FETCHED, handler_b)
        count = manager.emit_simple(EventType.PAGE_FETCHED, "Fetched")
        assert count == 2
        assert results["a"] == 1
        assert results["b"] == 1

    def test_global_handler(self):
        manager = NotificationManager()
        received = []

        manager.subscribe_all(lambda e: received.append(e))
        manager.emit_simple(EventType.PIPELINE_START, "Start")
        manager.emit_simple(EventType.PIPELINE_END, "End")
        assert len(received) == 2

    def test_unsubscribe(self):
        manager = NotificationManager()
        received = []

        def handler(event: PipelineEvent):
            received.append(event)

        manager.subscribe(EventType.CACHE_HIT, handler)
        manager.emit_simple(EventType.CACHE_HIT, "Hit 1")
        assert len(received) == 1

        manager.unsubscribe(EventType.CACHE_HIT, handler)
        manager.emit_simple(EventType.CACHE_HIT, "Hit 2")
        assert len(received) == 1  # no new events

    def test_event_log(self):
        manager = NotificationManager()
        manager.emit_simple(EventType.PAGE_FETCHED, "Page 1")
        manager.emit_simple(EventType.PAGE_CACHED, "Cache 1")
        log = manager.get_event_log()
        assert len(log) == 2

    def test_event_log_filtered(self):
        manager = NotificationManager()
        manager.emit_simple(EventType.PAGE_FETCHED, "Page 1")
        manager.emit_simple(EventType.PAGE_CACHED, "Cache 1")
        manager.emit_simple(EventType.PAGE_FETCHED, "Page 2")
        log = manager.get_event_log(event_type=EventType.PAGE_FETCHED)
        assert len(log) == 2

    def test_event_counts(self):
        manager = NotificationManager()
        manager.emit_simple(EventType.PAGE_FETCHED, "1")
        manager.emit_simple(EventType.PAGE_FETCHED, "2")
        manager.emit_simple(EventType.CACHE_HIT, "3")
        counts = manager.get_event_counts()
        assert counts["page_fetched"] == 2
        assert counts["cache_hit"] == 1

    def test_clear_log(self):
        manager = NotificationManager()
        manager.emit_simple(EventType.PIPELINE_START, "Start")
        assert manager.clear_log() == 1
        assert len(manager.get_event_log()) == 0

    def test_handler_count(self):
        manager = NotificationManager()
        manager.subscribe(EventType.PAGE_FETCHED, lambda e: None)
        manager.subscribe(EventType.PAGE_CACHED, lambda e: None)
        manager.subscribe_all(lambda e: None)
        assert manager.handler_count == 3

    def test_handler_exception_does_not_crash(self):
        manager = NotificationManager()

        def bad_handler(event: PipelineEvent):
            raise RuntimeError("Handler failed!")

        manager.subscribe(EventType.PIPELINE_START, bad_handler)
        # Should not raise
        count = manager.emit_simple(EventType.PIPELINE_START, "Test")
        assert count == 1

    def test_emit_with_data(self):
        manager = NotificationManager()
        received = []
        manager.subscribe_all(lambda e: received.append(e))
        manager.emit_simple(EventType.PAGE_FETCHED, "OK", url="https://example.com", status=200)
        assert received[0].data["url"] == "https://example.com"
        assert received[0].data["status"] == 200


class TestBuiltinHandlers:
    """Test the built-in handler factories."""

    def test_counter_handler(self):
        handler, get_counts = create_counter_handler()
        manager = NotificationManager()
        manager.subscribe_all(handler)
        manager.emit_simple(EventType.PAGE_FETCHED, "1")
        manager.emit_simple(EventType.PAGE_FETCHED, "2")
        manager.emit_simple(EventType.CACHE_HIT, "3")
        counts = get_counts()
        assert counts["page_fetched"] == 2
        assert counts["cache_hit"] == 1

    def test_file_handler(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        handler = create_file_handler(log_path)
        manager = NotificationManager()
        manager.subscribe_all(handler)
        manager.emit_simple(EventType.PIPELINE_START, "Begin")
        assert os.path.exists(log_path)
        with open(log_path, "r") as f:
            content = f.read()
        assert "pipeline_start" in content

    def test_console_handler(self, capsys):
        handler = create_console_handler(min_level=EventLevel.INFO)
        event = PipelineEvent(
            event_type=EventType.PIPELINE_START,
            level=EventLevel.INFO,
            message="Pipeline started!",
        )
        handler(event)
        captured = capsys.readouterr()
        assert "Pipeline started!" in captured.out

    def test_console_handler_filters_by_level(self, capsys):
        handler = create_console_handler(min_level=EventLevel.WARNING)
        debug_event = PipelineEvent(
            event_type=EventType.CUSTOM,
            level=EventLevel.DEBUG,
            message="Should be hidden",
        )
        handler(debug_event)
        captured = capsys.readouterr()
        assert captured.out == ""  # filtered out
