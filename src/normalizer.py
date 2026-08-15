"""
Data normalization module.
Transforms raw extracted strings into clean, typed Python representations.
"""

import re
from typing import Optional
from src.extract import RATING_MAP


def normalize_price(price_text: str) -> Optional[float]:
    """
    Extract numeric price in GBP from raw string (e.g. '£51.77' -> 51.77).
    Returns None if parsing fails.
    """
    if not price_text:
        return None
    # Remove currency symbols (e.g. £, $, €) and whitespace
    match = re.search(r"(\d+(?:\.\d+)?)", price_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def normalize_stock_count(availability_text: str) -> int:
    """
    Extract number of available items from availability string.
    e.g. 'In stock (22 available)' -> 22, 'In stock' -> 1, 'Out of stock' -> 0.
    """
    if not availability_text:
        return 0
    
    match = re.search(r"\((\d+)\s+available\)", availability_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    if "in stock" in availability_text.lower():
        return 1
    return 0


def normalize_rating(rating_text: str) -> int:
    """
    Map word rating (e.g. 'Three') to integer 1-5.
    Defaults to 0 if unknown.
    """
    return RATING_MAP.get(rating_text, 0)


def normalize_book_record(raw: dict) -> dict:
    """
    Normalize raw record dictionary ready for Pydantic schema validation.
    Maintains both raw values and clean normalized values side-by-side.
    """
    price_gbp = normalize_price(raw.get("price_text", ""))
    stock_count = normalize_stock_count(raw.get("availability_text", ""))
    rating = normalize_rating(raw.get("rating_text", ""))
    
    # Description clean up (normalize whitespace or keep None)
    desc = raw.get("description")
    if desc is not None:
        desc = desc.strip()
        if not desc:
            desc = None

    return {
        "title": raw.get("title", "").strip(),
        "product_url": raw.get("product_url", "").strip(),
        "price_text": raw.get("price_text", "").strip(),
        "price_gbp": price_gbp,
        "availability_text": raw.get("availability_text", "").strip(),
        "stock_count": stock_count,
        "rating_text": raw.get("rating_text", "").strip(),
        "rating": rating,
        "description": desc,
        "source_page": raw.get("source_page", "").strip(),
        "fetched_at": raw.get("fetched_at", ""),
    }
