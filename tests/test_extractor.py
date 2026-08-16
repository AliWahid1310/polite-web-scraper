"""
Unit tests for HTML detail extractor using saved test fixtures.
Tests valid HTML extraction, missing description handling, and malformed HTML resilience.
"""

import os
from src.extract import extract_book_detail
from src.storage import process_and_validate_records

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(filename: str) -> str:
    with open(os.path.join(FIXTURES_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


def test_extract_valid_fixture():
    """Test extracting all 8 raw fields from valid book fixture."""
    html = _read_fixture("book_valid.html")
    url = "https://books.toscrape.com/catalogue/clean-code_1/index.html"
    source = "https://books.toscrape.com/catalogue/page-1.html"

    record = extract_book_detail(html, url, source)
    assert record["title"] == "Clean Code: A Handbook of Agile Software Craftsmanship"
    assert record["price_text"] == "£37.50"
    assert record["availability_text"] == "In stock (14 available)"
    assert record["rating_text"] == "Four"
    assert "Even bad code can function" in record["description"]
    assert record["product_url"] == url
    assert record["source_page"] == source
    assert record["fetched_at"] is not None


def test_extract_missing_description_fixture():
    """Test that books without description return None, not invented text."""
    html = _read_fixture("book_missing_desc.html")
    url = "https://books.toscrape.com/catalogue/pragmatic-programmer_2/index.html"
    source = "https://books.toscrape.com/catalogue/page-1.html"

    record = extract_book_detail(html, url, source)
    assert record["title"] == "The Pragmatic Programmer"
    assert record["description"] is None
    assert record["price_text"] == "£42.00"
    assert record["rating_text"] == "Five"


def test_extract_malformed_fixture():
    """Test extraction resilience when parsing malformed HTML with weird whitespace."""
    html = _read_fixture("book_malformed.html")
    url = "https://books.toscrape.com/catalogue/refactoring_3/index.html"
    source = "https://books.toscrape.com/catalogue/page-1.html"

    record = extract_book_detail(html, url, source)
    assert "Refactoring" in record["title"]
    assert "89.99" in record["price_text"]
    assert record["rating_text"] == "Unknown"
    assert record["description"] is None


def test_duplicate_url_deduplication():
    """Test that identical product URLs are deduplicated during processing."""
    raw_records = [
        {
            "title": "Book One",
            "product_url": "https://books.toscrape.com/catalogue/book-1_1/index.html",
            "price_text": "£10.00",
            "availability_text": "In stock (5 available)",
            "rating_text": "Three",
            "description": "Desc",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "fetched_at": "2026-08-16T12:00:00Z",
        },
        {
            "title": "Book One (Duplicate)",
            "product_url": "https://books.toscrape.com/catalogue/book-1_1/index.html",
            "price_text": "£10.00",
            "availability_text": "In stock (5 available)",
            "rating_text": "Three",
            "description": "Desc",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "fetched_at": "2026-08-16T12:00:00Z",
        },
    ]
    valid, errors = process_and_validate_records(raw_records)
    assert len(valid) == 1
    assert len(errors) == 0
