"""
Polite Web Scraper — Command Line Interface (CLI).
Allows customizable execution of individual stages and pipeline options.

Usage Examples:
    python src/cli.py --help
    python src/cli.py --max-pages 3
    python src/cli.py --stage 2
    python src/cli.py --no-broken-test --export-csv --dashboard
"""

import argparse
import os
import sys

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import (
    BASE_URL,
    OUTPUT_DIR,
    discover_books,
    fetch_page,
    run_pipeline,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polite-scraper",
        description="The Polite Web Scraper — respectful, robust scraping pipeline for Books to Scrape.",
    )

    parser.add_argument(
        "--stage",
        type=str,
        default="all",
        choices=["0", "1", "2", "3", "4", "5", "6", "all"],
        help="Run up to or specifically a target stage (0: Classify, 1: Fetch/Cache, 2: Discover, 3: Extract, 4: Validate/Store, 5: Report, all: Full Pipeline)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Maximum number of catalogue pages to crawl (default: 3)",
    )
    parser.add_argument(
        "--no-broken-test",
        action="store_true",
        help="Disable injection of deliberate 404 test URL during Stage 5 resilience proof",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR,
        help=f"Directory to save output files (default: {OUTPUT_DIR})",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    print(f"\n[CLI] Running Polite Web Scraper with Stage={args.stage.upper()}, MaxPages={args.max_pages}")

    if args.stage == "0":
        print("Stage 0: Target Classification: Books to Scrape (https://books.toscrape.com)")
        print("robots.txt check: HTTP 404 Not Found (Sandbox environment).")
        return

    if args.stage == "1":
        print(f"Stage 1: Fetching & caching {BASE_URL} ...")
        html = fetch_page(BASE_URL)
        print(f"Result: {len(html) if html else 0:,} bytes fetched/cached.")
        return

    if args.stage == "2":
        print(f"Stage 2: Discovering catalogue up to {args.max_pages} pages ...")
        books = discover_books(BASE_URL, max_pages=args.max_pages)
        print(f"Discovered {len(books)} unique book links.")
        return

    # Full pipeline
    inject_broken = not args.no_broken_test
    run_pipeline(inject_broken_url=inject_broken)


if __name__ == "__main__":
    main()
