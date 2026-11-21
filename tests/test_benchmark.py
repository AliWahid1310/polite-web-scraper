"""
Unit tests for Pipeline Performance Benchmark Runner (src/benchmark.py).
"""

import os

from src.benchmark import PipelineBenchmark

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "book_valid.html")


def test_measure_parser_throughput():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    metrics = PipelineBenchmark.measure_parser_throughput(html, iterations=10)
    assert metrics["iterations"] == 10
    assert metrics["total_duration_sec"] > 0
    assert metrics["latency_per_page_ms"] > 0
    assert metrics["throughput_pages_per_sec"] > 0


def test_measure_function_execution():
    def dummy_task(x, y):
        return x + y

    res, elapsed = PipelineBenchmark.measure_function_execution(dummy_task, 10, 20)
    assert res == 30
    assert elapsed >= 0.0
