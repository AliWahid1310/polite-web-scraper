"""Tests for the multi-run dataset comparator (src/comparator.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.comparator import DatasetComparator


def _make_book(url: str, title: str = "Book", price: float = 10.0, stock: int = 5, rating: int = 3):
    return {
        "product_url": url,
        "title": title,
        "price_gbp": price,
        "stock_count": stock,
        "rating": rating,
        "availability_text": f"In stock ({stock} available)",
    }


class TestDatasetComparator:
    """Test the dataset comparator's diff capabilities."""

    def test_identical_datasets(self):
        books = [_make_book("https://example.com/a"), _make_book("https://example.com/b")]
        diff = DatasetComparator(books, books).compare()
        assert diff["added_count"] == 0
        assert diff["removed_count"] == 0
        assert diff["changed_count"] == 0
        assert diff["unchanged_count"] == 2

    def test_detect_additions(self):
        prev = [_make_book("https://example.com/a")]
        curr = [_make_book("https://example.com/a"), _make_book("https://example.com/b")]
        diff = DatasetComparator(prev, curr).compare()
        assert diff["added_count"] == 1
        assert diff["added"][0]["url"] == "https://example.com/b"

    def test_detect_removals(self):
        prev = [_make_book("https://example.com/a"), _make_book("https://example.com/b")]
        curr = [_make_book("https://example.com/a")]
        diff = DatasetComparator(prev, curr).compare()
        assert diff["removed_count"] == 1
        assert diff["removed"][0]["url"] == "https://example.com/b"

    def test_detect_price_change(self):
        prev = [_make_book("https://example.com/a", price=10.0)]
        curr = [_make_book("https://example.com/a", price=15.0)]
        diff = DatasetComparator(prev, curr).compare()
        assert diff["changed_count"] == 1
        changes = diff["changes"][0]["changes"]
        price_ch = [c for c in changes if c["field"] == "price_gbp"]
        assert len(price_ch) == 1
        assert price_ch[0]["previous"] == 10.0
        assert price_ch[0]["current"] == 15.0
        assert price_ch[0]["delta"] == 5.0

    def test_detect_stock_change(self):
        prev = [_make_book("https://example.com/a", stock=10)]
        curr = [_make_book("https://example.com/a", stock=3)]
        diff = DatasetComparator(prev, curr).compare()
        assert diff["changed_count"] == 1

    def test_detect_rating_change(self):
        prev = [_make_book("https://example.com/a", rating=3)]
        curr = [_make_book("https://example.com/a", rating=5)]
        diff = DatasetComparator(prev, curr).compare()
        assert diff["changed_count"] == 1

    def test_multiple_field_changes(self):
        prev = [_make_book("https://example.com/a", price=10.0, stock=5, rating=3)]
        curr = [_make_book("https://example.com/a", price=20.0, stock=0, rating=1)]
        diff = DatasetComparator(prev, curr).compare()
        changes = diff["changes"][0]["changes"]
        changed_fields = {c["field"] for c in changes}
        assert "price_gbp" in changed_fields
        assert "stock_count" in changed_fields
        assert "rating" in changed_fields

    def test_empty_datasets(self):
        diff = DatasetComparator([], []).compare()
        assert diff["previous_count"] == 0
        assert diff["current_count"] == 0

    def test_all_new(self):
        curr = [_make_book(f"https://example.com/{i}") for i in range(5)]
        diff = DatasetComparator([], curr).compare()
        assert diff["added_count"] == 5

    def test_all_removed(self):
        prev = [_make_book(f"https://example.com/{i}") for i in range(3)]
        diff = DatasetComparator(prev, []).compare()
        assert diff["removed_count"] == 3

    def test_get_price_changes(self):
        prev = [_make_book("https://example.com/a", price=10.0)]
        curr = [_make_book("https://example.com/a", price=12.0)]
        changes = DatasetComparator(prev, curr).get_price_changes()
        assert len(changes) == 1
        assert changes[0]["price_change"]["delta"] == 2.0

    def test_get_stock_changes(self):
        prev = [_make_book("https://example.com/a", stock=10)]
        curr = [_make_book("https://example.com/a", stock=5)]
        changes = DatasetComparator(prev, curr).get_stock_changes()
        assert len(changes) == 1
        assert changes[0]["stock_change"]["delta"] == -5

    def test_percent_change(self):
        prev = [_make_book("https://example.com/a", price=50.0)]
        curr = [_make_book("https://example.com/a", price=75.0)]
        diff = DatasetComparator(prev, curr).compare()
        price_change = [c for c in diff["changes"][0]["changes"] if c["field"] == "price_gbp"][0]
        assert price_change["percent_change"] == 50.0

    def test_summarize(self):
        prev = [_make_book("https://example.com/a", price=10.0)]
        curr = [_make_book("https://example.com/a", price=15.0), _make_book("https://example.com/b")]
        diff = DatasetComparator(prev, curr).compare()
        summary = DatasetComparator.summarize(diff)
        assert "Added:" in summary or "Changed" in summary
        assert isinstance(summary, str)

    def test_comparison_timestamp(self):
        diff = DatasetComparator([], []).compare()
        assert "comparison_timestamp" in diff
        assert "T" in diff["comparison_timestamp"]
