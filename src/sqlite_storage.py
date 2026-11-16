"""
SQLite Relational Storage and Query Engine.
Stores scraped book records into an indexed, relational SQLite database
with full search, filtering, and statistical aggregations.
"""

from __future__ import annotations

import sqlite3
from typing import Any


class SQLiteStorageManager:
    """
    Manages SQLite database storage for scraped book records.
    Provides indexing for fast lookup, filtering, and aggregations.
    """

    def __init__(self, db_path: str = "output/books.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    price_gbp REAL NOT NULL,
                    price_text TEXT NOT NULL,
                    currency TEXT DEFAULT 'GBP',
                    stock_count INTEGER NOT NULL,
                    is_in_stock INTEGER NOT NULL,
                    availability_text TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    rating_text TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    source_page TEXT NOT NULL,
                    total_inventory_value_gbp REAL NOT NULL,
                    fetched_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_price ON books(price_gbp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_rating ON books(rating)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_stock ON books(is_in_stock)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)")
            conn.commit()

    def upsert_books(self, records: list[dict[str, Any]]) -> int:
        """
        Upsert a list of book records idempotently.
        Returns the number of rows inserted or updated.
        """
        if not records:
            return 0

        inserted_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for r in records:
                cursor.execute("""
                    INSERT INTO books (
                        product_url, title, price_gbp, price_text, currency,
                        stock_count, is_in_stock, availability_text, rating,
                        rating_text, description, category, source_page,
                        total_inventory_value_gbp, fetched_at
                    ) VALUES (
                        :product_url, :title, :price_gbp, :price_text, :currency,
                        :stock_count, :is_in_stock, :availability_text, :rating,
                        :rating_text, :description, :category, :source_page,
                        :total_inventory_value_gbp, :fetched_at
                    )
                    ON CONFLICT(product_url) DO UPDATE SET
                        title = excluded.title,
                        price_gbp = excluded.price_gbp,
                        price_text = excluded.price_text,
                        currency = excluded.currency,
                        stock_count = excluded.stock_count,
                        is_in_stock = excluded.is_in_stock,
                        availability_text = excluded.availability_text,
                        rating = excluded.rating,
                        rating_text = excluded.rating_text,
                        description = excluded.description,
                        category = excluded.category,
                        source_page = excluded.source_page,
                        total_inventory_value_gbp = excluded.total_inventory_value_gbp,
                        fetched_at = excluded.fetched_at
                """, {
                    "product_url": str(r.get("product_url", "")),
                    "title": str(r.get("title", "")),
                    "price_gbp": float(r.get("price_gbp", 0.0)),
                    "price_text": str(r.get("price_text", "")),
                    "currency": str(r.get("currency", "GBP")),
                    "stock_count": int(r.get("stock_count", 0)),
                    "is_in_stock": 1 if r.get("stock_count", 0) > 0 else 0,
                    "availability_text": str(r.get("availability_text", "")),
                    "rating": int(r.get("rating", 0)),
                    "rating_text": str(r.get("rating_text", "")),
                    "description": r.get("description"),
                    "category": r.get("category"),
                    "source_page": str(r.get("source_page", "")),
                    "total_inventory_value_gbp": float(r.get("total_inventory_value_gbp", 0.0))
                    or round(float(r.get("price_gbp", 0.0)) * int(r.get("stock_count", 0)), 2),
                    "fetched_at": str(r.get("fetched_at", "")),
                })
                inserted_count += 1
            conn.commit()
        return inserted_count

    def query_books(
        self,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: int | None = None,
        in_stock_only: bool = False,
        search_term: str | None = None,
        order_by: str = "id",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query books with rich filtering, ordering, and pagination."""
        clauses = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if min_price is not None:
            clauses.append("price_gbp >= :min_price")
            params["min_price"] = min_price
        if max_price is not None:
            clauses.append("price_gbp <= :max_price")
            params["max_price"] = max_price
        if min_rating is not None:
            clauses.append("rating >= :min_rating")
            params["min_rating"] = min_rating
        if in_stock_only:
            clauses.append("is_in_stock = 1")
        if search_term:
            clauses.append("(title LIKE :search OR description LIKE :search)")
            params["search"] = f"%{search_term}%"

        where_stmt = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        # Validate order_by column
        allowed_orders = {
            "id": "id ASC",
            "price_asc": "price_gbp ASC",
            "price_desc": "price_gbp DESC",
            "rating_desc": "rating DESC",
            "title_asc": "title ASC",
            "stock_desc": "stock_count DESC",
        }
        order_stmt = allowed_orders.get(order_by, "id ASC")

        query = f"""
            SELECT product_url, title, price_gbp, price_text, currency,
                   stock_count, is_in_stock, availability_text, rating,
                   rating_text, description, category, source_page,
                   total_inventory_value_gbp, fetched_at
            FROM books
            {where_stmt}
            ORDER BY {order_stmt}
            LIMIT :limit OFFSET :offset
        """

        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            for row in cursor.execute(query, params):
                results.append(dict(row))
        return results

    def get_statistics(self) -> dict[str, Any]:
        """Return aggregate statistics from the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as total_books,
                    ROUND(AVG(price_gbp), 2) as avg_price,
                    MIN(price_gbp) as min_price,
                    MAX(price_gbp) as max_price,
                    SUM(stock_count) as total_units,
                    ROUND(SUM(total_inventory_value_gbp), 2) as total_valuation,
                    SUM(CASE WHEN is_in_stock = 1 THEN 1 ELSE 0 END) as in_stock_count
                FROM books
            """)
            row = cursor.fetchone()
            if row:
                return {
                    "total_books": row[0] or 0,
                    "avg_price": row[1] or 0.0,
                    "min_price": row[2] or 0.0,
                    "max_price": row[3] or 0.0,
                    "total_units": row[4] or 0,
                    "total_valuation_gbp": row[5] or 0.0,
                    "in_stock_count": row[6] or 0,
                }
            return {}
