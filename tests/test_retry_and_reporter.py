"""
Unit tests for retry policies and ScraperReporter metrics aggregation.
"""

import os
import tempfile
import requests
from src.reporter import ScraperReporter
from src.retry import should_retry
from src.schemas import BookRecord


def test_should_retry_rules():
    """Test retry decision matrix for status codes and exceptions."""
    # Never retry client definitive errors
    assert should_retry(404, None) is False
    assert should_retry(403, None) is False

    # Retry transient server errors
    assert should_retry(500, None) is True
    assert should_retry(502, None) is True
    assert should_retry(503, None) is True

    # Retry network timeouts and connection errors
    assert should_retry(None, requests.Timeout()) is True
    assert should_retry(None, requests.ConnectionError()) is True


def test_reporter_metrics_aggregation():
    """Test ScraperReporter statistics calculation and JSON generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        reporter = ScraperReporter(output_dir=temp_dir)
        reporter.start_run()

        reporter.record_network_fetch(is_cache_hit=True)
        reporter.record_network_fetch(is_cache_hit=False)
        reporter.record_failure("https://books.toscrape.com/broken", "HTTP 404", 404)

        dummy_record = BookRecord(
            title="Metrics Book",
            product_url="https://books.toscrape.com/catalogue/metrics_1/index.html",
            price_text="£20.00",
            price_gbp=20.00,
            availability_text="In stock (10 available)",
            stock_count=10,
            rating_text="Four",
            rating=4,
            description=None,
            source_page="https://books.toscrape.com/catalogue/page-1.html",
            fetched_at="2026-08-16T12:00:00Z",
        )

        report = reporter.finish_run(valid_records=[dummy_record], error_records=[])

        assert report["valid_records"] == 1
        assert report["invalid_records"] == 0
        assert report["failed_pages"] == 1
        assert report["cache_hits"] == 1
        assert report["network_requests"] == 1
        assert report["average_price_gbp"] == 20.00
        assert report["stock_total_units"] == 10
        assert os.path.exists(os.path.join(temp_dir, "run-report.json"))
