"""
Unit tests for SQLite Storage & Relational Query Engine (src/sqlite_storage.py).
"""

from src.sqlite_storage import SQLiteStorageManager


def test_sqlite_init_and_upsert(tmp_path):
    db_file = str(tmp_path / "test_books.db")
    manager = SQLiteStorageManager(db_path=db_file)

    sample_records = [
        {
            "product_url": "https://books.toscrape.com/catalogue/book-1.html",
            "title": "A Great Book",
            "price_gbp": 19.99,
            "price_text": "£19.99",
            "currency": "GBP",
            "stock_count": 12,
            "is_in_stock": True,
            "availability_text": "In stock (12 available)",
            "rating": 5,
            "rating_text": "Five",
            "description": "An engaging story of adventure.",
            "category": "Fiction",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "total_inventory_value_gbp": 239.88,
            "fetched_at": "2026-11-16T12:00:00Z",
        },
        {
            "product_url": "https://books.toscrape.com/catalogue/book-2.html",
            "title": "Second Book Adventure",
            "price_gbp": 35.50,
            "price_text": "£35.50",
            "currency": "GBP",
            "stock_count": 0,
            "is_in_stock": False,
            "availability_text": "Out of stock",
            "rating": 3,
            "rating_text": "Three",
            "description": "Historical analysis.",
            "category": "History",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "total_inventory_value_gbp": 0.0,
            "fetched_at": "2026-11-16T12:00:00Z",
        },
    ]

    count = manager.upsert_books(sample_records)
    assert count == 2

    # Query all
    all_books = manager.query_books()
    assert len(all_books) == 2
    assert all_books[0]["title"] == "A Great Book"

    # Query with filters
    fiction_only = manager.query_books(search_term="story")
    assert len(fiction_only) == 1
    assert fiction_only[0]["title"] == "A Great Book"

    high_rating = manager.query_books(min_rating=4)
    assert len(high_rating) == 1
    assert high_rating[0]["rating"] == 5

    in_stock = manager.query_books(in_stock_only=True)
    assert len(in_stock) == 1
    assert in_stock[0]["stock_count"] == 12

    price_filter = manager.query_books(min_price=20.0)
    assert len(price_filter) == 1
    assert price_filter[0]["title"] == "Second Book Adventure"


def test_sqlite_idempotent_upsert(tmp_path):
    db_file = str(tmp_path / "idempotent.db")
    manager = SQLiteStorageManager(db_path=db_file)

    rec = {
        "product_url": "https://books.toscrape.com/catalogue/book-1.html",
        "title": "Original Title",
        "price_gbp": 10.0,
        "price_text": "£10.00",
        "stock_count": 5,
        "availability_text": "In stock",
        "rating": 2,
        "rating_text": "Two",
        "source_page": "https://books.toscrape.com",
        "fetched_at": "2026-11-16T12:00:00Z",
    }
    manager.upsert_books([rec])

    # Update title and price
    rec_updated = dict(rec)
    rec_updated["title"] = "Updated Title"
    rec_updated["price_gbp"] = 15.0
    manager.upsert_books([rec_updated])

    results = manager.query_books()
    assert len(results) == 1
    assert results[0]["title"] == "Updated Title"
    assert results[0]["price_gbp"] == 15.0


def test_sqlite_statistics(tmp_path):
    db_file = str(tmp_path / "stats.db")
    manager = SQLiteStorageManager(db_path=db_file)

    recs = [
        {"product_url": "https://b.com/1", "title": "B1", "price_gbp": 10.0, "price_text": "£10", "stock_count": 5, "availability_text": "In stock", "rating": 3, "rating_text": "Three", "source_page": "p1", "fetched_at": "now", "total_inventory_value_gbp": 50.0},
        {"product_url": "https://b.com/2", "title": "B2", "price_gbp": 20.0, "price_text": "£20", "stock_count": 2, "availability_text": "In stock", "rating": 4, "rating_text": "Four", "source_page": "p1", "fetched_at": "now", "total_inventory_value_gbp": 40.0},
    ]
    manager.upsert_books(recs)
    stats = manager.get_statistics()

    assert stats["total_books"] == 2
    assert stats["avg_price"] == 15.0
    assert stats["min_price"] == 10.0
    assert stats["max_price"] == 20.0
    assert stats["total_units"] == 7
    assert stats["total_valuation_gbp"] == 90.0
    assert stats["in_stock_count"] == 2
