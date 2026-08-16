"""
Unit tests for data normalizer module.
Tests price normalization, stock extraction, rating conversions, and URL joining.
"""

from urllib.parse import urljoin
from src.normalizer import (
    normalize_book_record,
    normalize_price,
    normalize_rating,
    normalize_stock_count,
)


def test_price_normalization_standard():
    """Test standard GBP price string conversion."""
    assert normalize_price("£51.77") == 51.77
    assert normalize_price("£0.99") == 0.99
    assert normalize_price("£100.00") == 100.00


def test_price_normalization_with_whitespace_and_artifacts():
    """Test prices with surrounding whitespace and encoding noise."""
    assert normalize_price("  £42.50  ") == 42.50
    assert normalize_price("Â£19.99") == 19.99
    assert normalize_price("") is None
    assert normalize_price("Free") is None


def test_stock_count_normalization():
    """Test availability string parsing."""
    assert normalize_stock_count("In stock (22 available)") == 22
    assert normalize_stock_count("In stock (1 available)") == 1
    assert normalize_stock_count("In stock") == 1
    assert normalize_stock_count("Out of stock") == 0
    assert normalize_stock_count("") == 0


def test_rating_text_normalization():
    """Test mapping rating word to integer (1 to 5)."""
    assert normalize_rating("One") == 1
    assert normalize_rating("Two") == 2
    assert normalize_rating("Three") == 3
    assert normalize_rating("Four") == 4
    assert normalize_rating("Five") == 5
    assert normalize_rating("Unknown") == 0
    assert normalize_rating("") == 0


def test_urljoin_relative_to_absolute():
    """Test converting relative URLs to absolute URLs without string concatenation."""
    base_url = "https://books.toscrape.com/catalogue/page-1.html"
    relative_url = "a-light-in-the-attic_1000/index.html"
    absolute = urljoin(base_url, relative_url)
    assert absolute == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

    parent_relative = "../category/books_1/index.html"
    parent_absolute = urljoin(base_url, parent_relative)
    assert parent_absolute == "https://books.toscrape.com/category/books_1/index.html"


def test_normalize_book_record_comprehensive():
    """Test full record dictionary normalization."""
    raw = {
        "title": "  Python Crash Course  ",
        "product_url": "https://books.toscrape.com/catalogue/python-crash-course_1/index.html",
        "price_text": "£25.99",
        "availability_text": "In stock (12 available)",
        "rating_text": "Five",
        "description": "  A hands-on, project-based intro to programming.  ",
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-08-16T12:00:00Z",
    }
    normalized = normalize_book_record(raw)
    assert normalized["title"] == "Python Crash Course"
    assert normalized["price_gbp"] == 25.99
    assert normalized["stock_count"] == 12
    assert normalized["rating"] == 5
    assert normalized["description"] == "A hands-on, project-based intro to programming."
