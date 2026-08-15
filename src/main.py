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

import requests

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
# Main
# ---------------------------------------------------------------------------
def main():
    """Entry point for the scraping pipeline."""
    print("=" * 60)
    print("  The Polite Web Scraper")
    print("=" * 60)
    print()

    # Stage 1 — fetch the first catalogue page
    print("[Stage 1] Fetching first catalogue page ...")
    html = fetch_page(BASE_URL)
    if html:
        print(f"  [OK] Page fetched successfully ({len(html):,} bytes)")
    else:
        print("  [FAIL] Failed to fetch first catalogue page. Aborting.")
        return


if __name__ == "__main__":
    main()
