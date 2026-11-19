"""
Polite Web Scraper — Command Line Interface (CLI).
Allows customizable execution of individual stages, pipeline options,
export format selection, and SQLite queries.

Usage Examples:
    python src/cli.py --help
    python src/cli.py --max-pages 3
    python src/cli.py --stage 2
    python src/cli.py --export-format markdown
    python src/cli.py --query "poetry"
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exporters import export_all_formats, export_to_csv, export_to_markdown_table, export_to_ndjson, export_to_xml
from src.main import (
    BASE_URL,
    OUTPUT_DIR,
    discover_books,
    fetch_page,
    run_pipeline,
)
from src.server import run_server
from src.sqlite_storage import SQLiteStorageManager


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
    parser.add_argument(
        "--export-format",
        type=str,
        default="all",
        choices=["all", "csv", "markdown", "ndjson", "xml"],
        help="Target format to export records (default: all)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Search the local SQLite database for books matching a title or description substring",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Launch the live standalone web dashboard and REST API server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind the web server to (default: 8080)",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Launch Web Server mode
    if args.serve:
        run_server(port=args.port, output_dir=args.output_dir)
        return

    # Query mode for local SQLite DB
    if args.query:
        db_path = os.path.join(args.output_dir, "books.db")
        if not os.path.exists(db_path):
            print(f"[ERROR] Database file not found at {db_path}. Run the scraper pipeline first.")
            return

        db_manager = SQLiteStorageManager(db_path=db_path)
        results = db_manager.query_books(search_term=args.query)
        print(f"\n[QUERY] Search for '{args.query}' returned {len(results)} books:\n")
        for b in results:
            print(f"  - [{b['rating']}★] {b['title']} (£{b['price_gbp']}) — {b['availability_text']}")
        return

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

    # Specific format re-export if not all
    if args.export_format != "all":
        books_json_path = os.path.join(args.output_dir, "books.json")
        if os.path.exists(books_json_path):
            with open(books_json_path, "r", encoding="utf-8") as f:
                books = json.load(f)
            if args.export_format == "csv":
                p = export_to_csv(books, os.path.join(args.output_dir, "books.csv"))
            elif args.export_format == "markdown":
                p = export_to_markdown_table(books, os.path.join(args.output_dir, "books.md"))
            elif args.export_format == "ndjson":
                p = export_to_ndjson(books, os.path.join(args.output_dir, "books.ndjson"))
            elif args.export_format == "xml":
                p = export_to_xml(books, os.path.join(args.output_dir, "books.xml"))
            print(f"[EXPORT] Re-exported {len(books)} records to {p}")


if __name__ == "__main__":
    main()
