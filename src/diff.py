"""
Change detection and record hashing module.
Computes cryptographic digests of records to track changes across scraping runs.
Identifies: new records, modified records, unchanged records, and removed records.
"""

import hashlib
import json

from src.schemas import BookRecord


def hash_record(record: BookRecord | dict) -> str:
    """
    Generate a deterministic SHA-256 hash for a book's content fields
    (excluding volatile timestamps).
    """
    if isinstance(record, BookRecord):
        data = {
            "title": record.title,
            "product_url": str(record.product_url),
            "price_gbp": record.price_gbp,
            "stock_count": record.stock_count,
            "rating": record.rating,
            "description": record.description,
        }
    else:
        data = {
            "title": record.get("title"),
            "product_url": record.get("product_url"),
            "price_gbp": record.get("price_gbp"),
            "stock_count": record.get("stock_count"),
            "rating": record.get("rating"),
            "description": record.get("description"),
        }

    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def detect_changes(
    previous_records: list[dict],
    current_records: list[BookRecord] | list[dict],
) -> dict:
    """
    Compare current scrape results with previous baseline records.

    Returns:
        dict: {
            "new_count": int,
            "changed_count": int,
            "unchanged_count": int,
            "removed_count": int,
            "details": list[dict]
        }
    """
    prev_map = {r.get("product_url"): (r, hash_record(r)) for r in previous_records}
    curr_map = {}
    for r in current_records:
        url = str(r.product_url) if isinstance(r, BookRecord) else r.get("product_url")
        curr_map[url] = (r, hash_record(r))

    new_items = []
    changed_items = []
    unchanged_items = []
    removed_items = []

    for url, (record, curr_hash) in curr_map.items():
        if url not in prev_map:
            new_items.append({"url": url, "type": "NEW"})
        else:
            _, prev_hash = prev_map[url]
            if curr_hash == prev_hash:
                unchanged_items.append({"url": url, "type": "UNCHANGED"})
            else:
                changed_items.append({"url": url, "type": "CHANGED"})

    for url in prev_map:
        if url not in curr_map:
            removed_items.append({"url": url, "type": "REMOVED"})

    return {
        "new_count": len(new_items),
        "changed_count": len(changed_items),
        "unchanged_count": len(unchanged_items),
        "removed_count": len(removed_items),
        "total_current": len(curr_map),
    }
