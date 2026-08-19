"""
The Polite Web Scraper
======================
A robust, polite scraping pipeline for Books to Scrape (https://books.toscrape.com).

Stages:
0. Classify scraping target & robots policy
1. Fetch once, cache once with polite headers
2. Crawl 3 catalogue pages and discover unique URLs
3. Extract 8 raw fields with provenance
4. Normalize, validate schema (Pydantic), and store idempotently
5. Handle failures gracefully, polite retries, and honest run report
6. Publish reproducible evidence
"""

import hashlib
import json
import os
import re
import sys
import time
from urllib.parse import urljoin

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

from src.dashboard import generate_dashboard_html
from src.exporters import export_to_csv
from src.extract import extract_book_detail
from src.logger import StructuredLogger
from src.reporter import ScraperReporter
from src.retry import polite_get_with_retry
from src.storage import process_and_validate_records, save_records

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
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# A deliberately broken test URL for Stage 5 resilience proof
TEST_BROKEN_URL = "https://books.toscrape.com/catalogue/deliberately-broken-page-404_99999/index.html"


# ---------------------------------------------------------------------------
# Stage 1 & 5 — Fetch once, cache once, retry politely on transient errors
# ---------------------------------------------------------------------------
def _cache_path(url: str) -> str:
    """Return a filesystem-safe cache path for a given URL."""
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", url)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    filename = f"{safe_name[:80]}_{url_hash}.html"
    return os.path.join(CACHE_DIR, filename)


def fetch_page(url: str, reporter: ScraperReporter | None = None) -> str | None:
    """
    Fetch a page politely with caching and retry capability.

    - If cached: read from cache, log CACHE HIT, zero network traffic.
    - If not cached: HTTP GET with custom user-agent, timeout, and transient retry.
    """
    cached = _cache_path(url)

    if os.path.exists(cached):
        with open(cached, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"  CACHE HIT  {url}  ({len(html):,} bytes)")
        if reporter:
            reporter.record_network_fetch(is_cache_hit=True)
        return html

    if reporter:
        reporter.record_network_fetch(is_cache_hit=False)

    resp, status_code, exc = polite_get_with_retry(
        url=url,
        user_agent=USER_AGENT,
        timeout=REQUEST_TIMEOUT,
        max_retries=1,
    )

    if exc:
        print(f"  FETCH FAIL {url}  (Exception: {exc})")
        if reporter:
            reporter.record_failure(url, f"Network exception: {exc}")
        return None

    if not resp or status_code != 200:
        print(f"  FETCH FAIL {url}  (Status: {status_code})")
        if reporter:
            reporter.record_failure(url, f"HTTP {status_code}", status_code)
        return None

    if resp.encoding == "ISO-8859-1" or not resp.encoding:
        resp.encoding = resp.apparent_encoding or "utf-8"

    html = resp.text

    # Save to disk cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cached, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  FETCH      {url}  ({len(html):,} bytes)")
    time.sleep(POLITENESS_DELAY)
    return html


# ---------------------------------------------------------------------------
# Stage 2 — Find all three catalogue pages
# ---------------------------------------------------------------------------
def discover_books(
    start_url: str,
    max_pages: int = MAX_CATALOGUE_PAGES,
    reporter: ScraperReporter | None = None,
) -> list[dict]:
    """
    Crawl catalogue pages and collect book URLs.
    Follows the 'next' link up to max_pages. Deduplicates URLs.
    """
    all_books = []
    seen_urls = set()
    current_url = start_url
    pages_crawled = 0

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        print(f"  Catalogue page {pages_crawled}: {current_url}")

        html = fetch_page(current_url, reporter=reporter)
        if html is None:
            print(f"  [FAIL] Could not fetch catalogue page {pages_crawled}")
            break

        if reporter:
            reporter.metrics.catalogue_pages_fetched += 1

        soup = BeautifulSoup(html, "lxml")

        for article in soup.select("article.product_pod"):
            link_tag = article.select_one("h3 > a")
            if link_tag and link_tag.get("href"):
                absolute_url = urljoin(current_url, link_tag["href"])
                if absolute_url not in seen_urls:
                    seen_urls.add(absolute_url)
                    all_books.append({
                        "url": absolute_url,
                        "source_page": current_url,
                    })

        next_link = soup.select_one("li.next > a")
        if next_link and next_link.get("href"):
            current_url = urljoin(current_url, next_link["href"])
        else:
            current_url = None

    if reporter:
        reporter.metrics.catalogue_pages_discovered = pages_crawled
        reporter.metrics.detail_pages_discovered = len(all_books)

    print(f"\n  catalogue_pages={pages_crawled}  discovered={len(all_books)}  unique_urls={len(seen_urls)}")
    return all_books


# ---------------------------------------------------------------------------
# Stage 3 & 5 — Extract raw records with isolated failure handling
# ---------------------------------------------------------------------------
def extract_all_raw_records(
    book_entries: list[dict],
    reporter: ScraperReporter | None = None,
) -> list[dict]:
    """
    Fetch and extract 8 raw fields for all discovered books.
    Each page is isolated in try-except: broken pages are logged & skipped.
    """
    raw_records = []
    print(f"[Stage 3 & 5] Extracting raw details for {len(book_entries)} books ...")

    for entry in book_entries:
        url = entry["url"]
        source_page = entry["source_page"]

        try:
            html = fetch_page(url, reporter=reporter)
            if not html:
                print(f"  [SKIP] Skipping unretrievable page: {url}")
                continue

            record = extract_book_detail(html, url, source_page)
            raw_records.append(record)
            if reporter:
                reporter.metrics.detail_pages_fetched += 1

        except Exception as exc:
            print(f"  [ERROR] Unhandled parser failure for {url}: {exc}")
            if reporter:
                reporter.record_failure(url, f"Parser error: {exc}")
            continue

    print(f"\n  detail_pages_extracted={len(raw_records)}")
    return raw_records


# ---------------------------------------------------------------------------
# Main Orchestration Pipeline
# ---------------------------------------------------------------------------
def run_pipeline(inject_broken_url: bool = True) -> tuple[dict, dict]:
    """
    Execute the full polite scraping pipeline end-to-end.
    """
    logger = StructuredLogger(log_path=os.path.join(OUTPUT_DIR, "scraper.log.jsonl"))
    logger.info("PIPELINE_START", base_url=BASE_URL, max_pages=MAX_CATALOGUE_PAGES)

    reporter = ScraperReporter(output_dir=OUTPUT_DIR)
    reporter.start_run()

    print("=" * 60)
    print("  The Polite Web Scraper Pipeline")
    print("=" * 60)
    print()

    # Stage 2: Discover catalogue
    print("[Stage 2] Discovering books from catalogue pages ...")
    book_entries = discover_books(BASE_URL, reporter=reporter)
    if not book_entries:
        print("  [FAIL] No books discovered. Aborting.")
        logger.error("CATALOGUE_DISCOVERY_FAILED", base_url=BASE_URL)
        reporter.finish_run([], [])
        return {}, {}
    print(f"  [OK] {len(book_entries)} unique book URLs collected\n")
    logger.info("CATALOGUE_DISCOVERY_COMPLETE", count=len(book_entries))

    # Stage 5 resilience demonstration: inject 1 broken URL
    if inject_broken_url:
        print("[Stage 5 Resilience Test] Injecting 1 test broken URL ...")
        book_entries.append({
            "url": TEST_BROKEN_URL,
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        })
        logger.warn("INJECTED_TEST_BROKEN_URL", url=TEST_BROKEN_URL)

    # Stage 3 & 5: Extract raw records
    raw_records = extract_all_raw_records(book_entries, reporter=reporter)
    print(f"  [OK] Detail extraction complete: {len(raw_records)} records\n")
    logger.info("DETAIL_EXTRACTION_COMPLETE", count=len(raw_records))

    # Stage 4: Normalize, validate, store
    print("[Stage 4] Normalizing and schema-validating records ...")
    valid_records, error_records = process_and_validate_records(raw_records)
    save_result = save_records(valid_records, error_records, output_dir=OUTPUT_DIR)
    logger.info("RECORDS_VALIDATED_AND_STORED", valid=len(valid_records), errors=len(error_records))

    # Extras: CSV Export
    csv_file = export_to_csv(valid_records, output_path=os.path.join(OUTPUT_DIR, "books.csv"))

    print(f"  Valid records saved: {save_result['books_saved']} -> {save_result['books_file']}")
    print(f"  CSV export saved:    {len(valid_records)} -> {csv_file}")
    print(f"  Invalid records:     {save_result['errors_saved']} -> {save_result['errors_file']}")
    print(f"  [OK] Stage 4 complete: {len(valid_records)} verified records stored.\n")

    # Stage 5: Finalize report
    print("[Stage 5] Generating run report ...")
    report_data = reporter.finish_run(valid_records, error_records)
    report_path = os.path.join(OUTPUT_DIR, "run-report.json")
    print(f"  [OK] Report saved to {report_path}")

    # Extras: Generate Visual Dashboard
    dashboard_path = generate_dashboard_html(
        books_json_path=os.path.join(OUTPUT_DIR, "books.json"),
        report_json_path=report_path,
        output_html_path=os.path.join(OUTPUT_DIR, "dashboard.html"),
    )
    print(f"  [OK] Visual dashboard saved to {dashboard_path}\n")
    print(json.dumps(report_data, indent=2))

    return save_result, report_data


if __name__ == "__main__":
    run_pipeline(inject_broken_url=True)
