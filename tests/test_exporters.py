"""
Unit tests for CSV exporter module (src/exporters.py).
"""

import csv
import os
import tempfile
from datetime import datetime, timezone
from pydantic import HttpUrl
from src.exporters import export_to_csv
from src.schemas import BookRecord


def test_export_to_csv_creates_clean_tabular_file():
    """Test exporting validated BookRecords to standard CSV with flattened fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "books.csv")

        records = [
            BookRecord(
                title="CSV Book 1",
                product_url=HttpUrl("https://books.toscrape.com/catalogue/csv-book-1/index.html"),
                price_text="£12.50",
                price_gbp=12.50,
                availability_text="In stock (8 available)",
                stock_count=8,
                rating_text="Four",
                rating=4,
                description="Line 1.\nLine 2 with spaces.",
                source_page=HttpUrl("https://books.toscrape.com/catalogue/page-1.html"),
                fetched_at=datetime.now(timezone.utc),
            )
        ]

        result_path = export_to_csv(records, output_path=csv_path)
        assert os.path.exists(result_path)

        with open(result_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["title"] == "CSV Book 1"
        assert rows[0]["price_gbp"] == "12.5"
        assert rows[0]["stock_count"] == "8"
        assert "Line 1. Line 2 with spaces." in rows[0]["description"]
