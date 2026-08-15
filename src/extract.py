"""
HTML extraction module for book detail pages.
Extracts raw fields without loss or premature conversion.
"""

from datetime import datetime, timezone
from bs4 import BeautifulSoup

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def extract_rating_text(soup: BeautifulSoup) -> str:
    """Extract rating text (e.g. 'Three') from star-rating class."""
    rating_tag = soup.select_one("p.star-rating")
    if not rating_tag:
        return "Unknown"
    
    classes = rating_tag.get("class", [])
    for cls in classes:
        if cls in RATING_MAP:
            return cls
    return "Unknown"


def extract_book_detail(html: str, product_url: str, source_page: str) -> dict:
    """
    Extract the 8 raw fields from a book's detail page HTML.
    
    Returns:
        dict: {
            "title": str,
            "product_url": str,
            "price_text": str,
            "availability_text": str,
            "rating_text": str,
            "description": str | None,
            "source_page": str,
            "fetched_at": str (ISO 8601 UTC)
        }
    """
    soup = BeautifulSoup(html, "lxml")
    product_main = soup.select_one("div.product_main")

    # Title
    title = ""
    if product_main:
        h1 = product_main.select_one("h1")
        if h1:
            title = h1.get_text(strip=True)

    # Price text (e.g. '£51.77')
    price_text = ""
    if product_main:
        price_tag = product_main.select_one("p.price_color")
        if price_tag:
            price_text = price_tag.get_text(strip=True)

    # Availability text (e.g. 'In stock (22 available)')
    availability_text = ""
    if product_main:
        avail_tag = product_main.select_one("p.instock.availability")
        if avail_tag:
            availability_text = " ".join(avail_tag.get_text().split())

    # Star rating
    rating_text = extract_rating_text(soup)

    # Description (can be None for some books)
    description = None
    desc_header = soup.select_one("#product_description")
    if desc_header:
        # Description is the next sibling paragraph
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            description = desc_p.get_text(strip=True)

    # Provenance
    fetched_at = datetime.now(timezone.utc).isoformat()

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
