"""
Unit tests for Pydantic BookRecord schema validation.
Tests strict type constraints, edge cases, and rejection of invalid records.
"""

import pytest
from pydantic import ValidationError
from src.schemas import BookRecord


def test_book_record_valid():
    """Test valid BookRecord creation."""
    record = BookRecord(
        title="Automate the Boring Stuff",
        product_url="https://books.toscrape.com/catalogue/automate-the-boring-stuff_1/index.html",
        price_text="£29.95",
        price_gbp=29.95,
        availability_text="In stock (10 available)",
        stock_count=10,
        rating_text="Five",
        rating=5,
        description="Learn practical Python programming.",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-08-16T12:00:00Z",
    )
    assert record.title == "Automate the Boring Stuff"
    assert record.price_gbp == 29.95
    assert record.rating == 5
    assert record.description == "Learn practical Python programming."


def test_book_record_optional_description_as_none():
    """Test BookRecord with None description (acceptable by schema)."""
    record = BookRecord(
        title="Book Without Description",
        product_url="https://books.toscrape.com/catalogue/no-desc_1/index.html",
        price_text="£15.00",
        price_gbp=15.00,
        availability_text="In stock",
        stock_count=1,
        rating_text="Three",
        rating=3,
        description=None,
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-08-16T12:00:00Z",
    )
    assert record.description is None


def test_book_record_reject_blank_title():
    """Test rejection of empty or blank whitespace-only title."""
    with pytest.raises(ValidationError):
        BookRecord(
            title="   ",
            product_url="https://books.toscrape.com/catalogue/blank_1/index.html",
            price_text="£10.00",
            price_gbp=10.00,
            availability_text="In stock",
            stock_count=1,
            rating_text="Three",
            rating=3,
            description=None,
            source_page="https://books.toscrape.com/catalogue/page-1.html",
            fetched_at="2026-08-16T12:00:00Z",
        )


def test_book_record_reject_invalid_price():
    """Test rejection of zero or negative price."""
    with pytest.raises(ValidationError):
        BookRecord(
            title="Free Book",
            product_url="https://books.toscrape.com/catalogue/free_1/index.html",
            price_text="£0.00",
            price_gbp=0.00,  # gt=0.0 constraint
            availability_text="In stock",
            stock_count=1,
            rating_text="Three",
            rating=3,
            description=None,
            source_page="https://books.toscrape.com/catalogue/page-1.html",
            fetched_at="2026-08-16T12:00:00Z",
        )


def test_book_record_reject_invalid_rating():
    """Test rejection of rating out of bounds (must be 1-5)."""
    with pytest.raises(ValidationError):
        BookRecord(
            title="Super Book",
            product_url="https://books.toscrape.com/catalogue/super_1/index.html",
            price_text="£10.00",
            price_gbp=10.00,
            availability_text="In stock",
            stock_count=1,
            rating_text="Six",
            rating=6,  # le=5 constraint
            description=None,
            source_page="https://books.toscrape.com/catalogue/page-1.html",
            fetched_at="2026-08-16T12:00:00Z",
        )
