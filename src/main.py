"""
The Polite Web Scraper
======================
A polite scraping pipeline for Books to Scrape (https://books.toscrape.com).

Downloads the first 3 catalogue pages, visits all 60 book detail pages,
extracts and validates records into clean JSON, and produces a run report.
"""

import os
import re
import time
import hashlib
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = (
    "PoliteWebScraper/1.0 "
    "(+https://github.com/AliWahid1310/polite-web-scraper)"
)
REQUEST_TIMEOUT = 10  # seconds
POLITENESS_DELAY = 0.5  # seconds between real (non-cached) requests
MAX_CATALOGUE_PAGES = 3
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")


# ---------------------------------------------------------------------------
# Stage 1 — Fetch once, cache once
# ---------------------------------------------------------------------------
def _cache_path(url: str) -> str:
    """Return a filesystem-safe cache path for a given URL."""
    # Use a hash to avoid filesystem issues with long/special-char URLs
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", url)
    # Keep it short but unique by appending a hash
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    filename = f"{safe_name[:80]}_{url_hash}.html"
    return os.path.join(CACHE_DIR, filename)


def fetch_page(url: str) -> str | None:
    """
    Fetch a page, using the cache when available.

    - First run: sends a real HTTP request, saves to cache/, prints FETCH.
    - Subsequent runs: reads from cache/, prints CACHE HIT.
    - Returns the HTML string, or None on failure.
    """
    cached = _cache_path(url)

    # Check cache first
    if os.path.exists(cached):
        with open(cached, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"  CACHE HIT  {url}  ({len(html):,} bytes)")
        return html

    # Real fetch — be polite
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        print(f"  FETCH FAIL {url}  ({exc})")
        return None

    if response.status_code != 200:
        print(f"  FETCH FAIL {url}  (status {response.status_code})")
        return None

    html = response.text

    # Save to cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cached, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  FETCH      {url}  ({len(html):,} bytes)")

    # Politeness delay after a real request
    time.sleep(POLITENESS_DELAY)

    return html


# ---------------------------------------------------------------------------
# Stage 2 — Find all three pages
# ---------------------------------------------------------------------------
def discover_books(start_url: str, max_pages: int = MAX_CATALOGUE_PAGES) -> list[dict]:
    """
    Crawl catalogue pages and collect book URLs.

    Returns a list of dicts: {"url": <absolute_url>, "source_page": <catalogue_page_url>}
    Follows the 'next' link up to max_pages. Deduplicates by URL.
    """
    all_books = []
    seen_urls = set()
    current_url = start_url
    pages_crawled = 0

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        print(f"  Catalogue page {pages_crawled}: {current_url}")

        html = fetch_page(current_url)
        if html is None:
            print(f"  [FAIL] Could not fetch catalogue page {pages_crawled}")
            break

        soup = BeautifulSoup(html, "lxml")

        # Collect book links from article.product_pod h3 > a
        for article in soup.select("article.product_pod"):
            link_tag = article.select_one("h3 > a")
            if link_tag and link_tag.get("href"):
                # Convert relative URL to absolute using urljoin
                absolute_url = urljoin(current_url, link_tag["href"])
                if absolute_url not in seen_urls:
                    seen_urls.add(absolute_url)
                    all_books.append({
                        "url": absolute_url,
                        "source_page": current_url,
                    })

        # Follow the 'next' link
        next_link = soup.select_one("li.next > a")
        if next_link and next_link.get("href"):
            current_url = urljoin(current_url, next_link["href"])
        else:
            current_url = None

    total_discovered = len(all_books)
    unique_count = len(seen_urls)
    print(f"\n  catalogue_pages={pages_crawled}  discovered={total_discovered}  unique_urls={unique_count}")

    return all_books


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Entry point for the scraping pipeline."""
    print("=" * 60)
    print("  The Polite Web Scraper")
    print("=" * 60)
    print()

    # Stage 2 — discover books across 3 catalogue pages
    print("[Stage 2] Discovering books from catalogue pages ...")
    book_entries = discover_books(BASE_URL)
    if not book_entries:
        print("  [FAIL] No books discovered. Aborting.")
        return
    print(f"  [OK] {len(book_entries)} unique book URLs collected\n")


if __name__ == "__main__":
    main()

