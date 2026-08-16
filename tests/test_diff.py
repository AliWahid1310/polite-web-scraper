"""
Unit tests for change detection and hashing module (diff.py).
"""

from src.diff import detect_changes, hash_record


def test_hash_record_deterministic():
    """Test that identical data produces the same SHA-256 hash."""
    rec1 = {
        "title": "Title A",
        "product_url": "https://books.toscrape.com/a",
        "price_gbp": 10.0,
        "stock_count": 5,
        "rating": 3,
        "description": "Desc",
    }
    rec2 = {
        "title": "Title A",
        "product_url": "https://books.toscrape.com/a",
        "price_gbp": 10.0,
        "stock_count": 5,
        "rating": 3,
        "description": "Desc",
    }
    assert hash_record(rec1) == hash_record(rec2)


def test_detect_changes_lifecycle():
    """Test detecting NEW, CHANGED, UNCHANGED, and REMOVED records."""
    baseline = [
        {"title": "Book 1", "product_url": "https://books.toscrape.com/1", "price_gbp": 10.0, "stock_count": 5, "rating": 3, "description": "D1"},
        {"title": "Book 2", "product_url": "https://books.toscrape.com/2", "price_gbp": 20.0, "stock_count": 2, "rating": 4, "description": "D2"},
    ]

    current = [
        # Unchanged
        {"title": "Book 1", "product_url": "https://books.toscrape.com/1", "price_gbp": 10.0, "stock_count": 5, "rating": 3, "description": "D1"},
        # Changed price
        {"title": "Book 2", "product_url": "https://books.toscrape.com/2", "price_gbp": 25.0, "stock_count": 2, "rating": 4, "description": "D2"},
        # New book
        {"title": "Book 3", "product_url": "https://books.toscrape.com/3", "price_gbp": 15.0, "stock_count": 1, "rating": 5, "description": "D3"},
    ]

    diff_result = detect_changes(baseline, current)
    assert diff_result["unchanged_count"] == 1
    assert diff_result["changed_count"] == 1
    assert diff_result["new_count"] == 1
    assert diff_result["removed_count"] == 0
