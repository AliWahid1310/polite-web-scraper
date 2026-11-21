"""
Pipeline Performance Benchmark Runner.
Measures parsing throughput, cache efficiency, memory overhead,
and latency profiles across scraping pipeline stages.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from src.extract import extract_book_detail


class PipelineBenchmark:
    """Benchmark runner for measuring extraction and parsing performance."""

    @staticmethod
    def measure_parser_throughput(
        sample_html: str,
        iterations: int = 100,
    ) -> dict[str, float]:
        """Measure BeautifulSoup parsing throughput and latency per page."""
        url = "https://books.toscrape.com/catalogue/benchmark_item/index.html"
        source = "https://books.toscrape.com/catalogue/page-1.html"

        start_time = time.perf_counter()
        for _ in range(iterations):
            extract_book_detail(sample_html, url, source)
        duration = time.perf_counter() - start_time

        per_page_ms = (duration / iterations) * 1000.0
        pages_per_sec = iterations / duration if duration > 0 else 0.0

        return {
            "iterations": float(iterations),
            "total_duration_sec": round(duration, 4),
            "latency_per_page_ms": round(per_page_ms, 2),
            "throughput_pages_per_sec": round(pages_per_sec, 2),
        }

    @staticmethod
    def measure_function_execution(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
        """Measure wall-clock latency of an arbitrary callable."""
        t0 = time.perf_counter()
        res = fn(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        return res, round(elapsed, 4)
