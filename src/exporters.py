"""
Export utility module.
Produces flattened CSV records from schema-validated BookRecords.
"""

import csv
import os
from src.schemas import BookRecord


def export_to_csv(records: list[BookRecord], output_path: str = "output/books.csv") -> str:
    """
    Export validated records into a standard CSV format.
    Flattens HttpUrl, datetime, and multiline descriptions for clean tabular consumption.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "title",
        "product_url",
        "price_gbp",
        "price_text",
        "stock_count",
        "availability_text",
        "rating",
        "rating_text",
        "description",
        "source_page",
        "fetched_at",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for record in records:
            # Flatten multiline description to single line for CSV cleanliness
            desc = record.description or ""
            desc_clean = " ".join(desc.split())

            writer.writerow({
                "title": record.title,
                "product_url": str(record.product_url),
                "price_gbp": record.price_gbp,
                "price_text": record.price_text,
                "stock_count": record.stock_count,
                "availability_text": record.availability_text,
                "rating": record.rating,
                "rating_text": record.rating_text,
                "description": desc_clean,
                "source_page": str(record.source_page),
                "fetched_at": record.fetched_at.isoformat(),
            })

    return output_path
