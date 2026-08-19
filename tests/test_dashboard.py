"""
Unit tests for local HTML dashboard generator (src/dashboard.py).
"""

import json
import os
import tempfile
from src.dashboard import generate_dashboard_html


def test_generate_dashboard_html_structure():
    """Test generating standalone HTML dashboard with embedded JSON data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        books_file = os.path.join(tmpdir, "books.json")
        report_file = os.path.join(tmpdir, "run-report.json")
        html_out = os.path.join(tmpdir, "dashboard.html")

        sample_books = [
            {
                "title": "Dashboard Book",
                "product_url": "https://books.toscrape.com/catalogue/dash_1/index.html",
                "price_text": "£25.00",
                "price_gbp": 25.0,
                "availability_text": "In stock (10 available)",
                "stock_count": 10,
                "rating_text": "Five",
                "rating": 5,
                "description": "A great test book.",
                "source_page": "https://books.toscrape.com/catalogue/page-1.html",
                "fetched_at": "2026-08-19T12:00:00Z",
            }
        ]
        sample_report = {
            "end_time": "2026-08-19T12:00:00Z",
            "duration_seconds": 1.5,
            "catalogue_pages_fetched": 3,
            "cache_hits": 60,
            "failed_pages": 0,
        }

        with open(books_file, "w", encoding="utf-8") as f:
            json.dump(sample_books, f)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(sample_report, f)

        res_path = generate_dashboard_html(
            books_json_path=books_file,
            report_json_path=report_file,
            output_html_path=html_out,
        )

        assert os.path.exists(res_path)
        with open(res_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "<!DOCTYPE html>" in content
        assert "The Polite Scraper" in content
        assert "Dashboard Book" in content
        assert "£25.00" in content
