"""
Pipeline storage and validation module.
Enforces Pydantic schema validation, separates invalid records into errors.json,
and guarantees idempotent writing to output/books.json.
"""

import json
import os
from datetime import datetime, timezone
from pydantic import ValidationError

from src.normalizer import normalize_book_record
from src.schemas import BookRecord, ErrorRecord

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
BOOKS_FILE = os.path.join(OUTPUT_DIR, "books.json")
ERRORS_FILE = os.path.join(OUTPUT_DIR, "errors.json")


def process_and_validate_records(
    raw_records: list[dict],
) -> tuple[list[BookRecord], list[ErrorRecord]]:
    """
    Normalize and validate raw scraped records.
    Deduplicates records by canonical product_url.
    
    Returns:
        tuple (valid_records, error_records)
    """
    valid_records: list[BookRecord] = []
    error_records: list[ErrorRecord] = []
    seen_canonical_urls: set[str] = set()

    for raw in raw_records:
        normalized = normalize_book_record(raw)
        canonical_url = normalized.get("product_url", "")

        # Canonical deduplication check
        if canonical_url in seen_canonical_urls:
            continue

        try:
            # Pydantic schema validation
            record = BookRecord(**normalized)
            valid_records.append(record)
            seen_canonical_urls.add(canonical_url)
        except ValidationError as err:
            reasons = [f"{e['loc']}: {e['msg']}" for e in err.errors()]
            error_rec = ErrorRecord(
                raw_record=raw,
                reasons=reasons,
                rejected_at=datetime.now(timezone.utc).isoformat(),
            )
            error_records.append(error_rec)

    return valid_records, error_records


def save_records(
    valid_records: list[BookRecord],
    error_records: list[ErrorRecord],
    output_dir: str = OUTPUT_DIR,
) -> dict:
    """
    Persist valid records to output/books.json and errors to output/errors.json.
    Idempotent operation (overwrites previous runs cleanly).
    """
    os.makedirs(output_dir, exist_ok=True)
    books_path = os.path.join(output_dir, "books.json")
    errors_path = os.path.join(output_dir, "errors.json")

    # Serialize valid records
    serializable_books = [
        json.loads(record.model_dump_json()) for record in valid_records
    ]
    with open(books_path, "w", encoding="utf-8") as f:
        json.dump(serializable_books, f, indent=2, ensure_ascii=False)

    # Serialize error records
    serializable_errors = [
        err.model_dump() for err in error_records
    ]
    with open(errors_path, "w", encoding="utf-8") as f:
        json.dump(serializable_errors, f, indent=2, ensure_ascii=False)

    return {
        "books_saved": len(valid_records),
        "errors_saved": len(error_records),
        "books_file": books_path,
        "errors_file": errors_path,
    }
