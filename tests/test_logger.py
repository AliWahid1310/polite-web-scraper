"""
Unit tests for structured JSON-Lines logger module (src/logger.py).
"""

import json
import os
import tempfile
from src.logger import StructuredLogger


def test_structured_logger_emits_valid_jsonl():
    """Test that logger writes valid JSONL objects with timestamp and event."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log.jsonl")
        logger = StructuredLogger(log_path=log_file)

        logger.info("TEST_EVENT_1", stage="stage_1", count=42)
        logger.warn("TEST_WARNING", reason="test warning")
        logger.error("TEST_ERROR", code=500)

        assert os.path.exists(log_file)

        with open(log_file, "r", encoding="utf-8") as f:
            lines = [json.loads(line.strip()) for line in f if line.strip()]

        assert len(lines) == 3
        assert lines[0]["event"] == "TEST_EVENT_1"
        assert lines[0]["level"] == "INFO"
        assert lines[0]["count"] == 42
        assert "timestamp" in lines[0]

        assert lines[1]["level"] == "WARN"
        assert lines[2]["level"] == "ERROR"
