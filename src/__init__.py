"""
Polite Web Scraper package.
A robust, respectful, production-grade scraping pipeline for Books to Scrape.
"""

from __future__ import annotations

__version__ = "2.0.0"
__author__ = "AliWahid1310"

from src.analytics import calculate_price_statistics, generate_full_analytics_summary
from src.audit import DatasetAuditor
from src.dashboard import generate_dashboard_html
from src.exporters import export_all_formats, export_to_csv, export_to_markdown_table
from src.extract import extract_book_detail
from src.headers import RespectfulHeaderManager
from src.normalizer import normalize_book_record
from src.rate_limiter import TokenBucketRateLimiter
from src.reporter import ScraperReporter
from src.retry import polite_get_with_retry
from src.schemas import BookRecord, ErrorRecord
from src.sqlite_storage import SQLiteStorageManager
from src.storage import process_and_validate_records, save_records
from src.terminal_ui import TerminalUI

__all__ = [
    "BookRecord",
    "DatasetAuditor",
    "ErrorRecord",
    "RespectfulHeaderManager",
    "SQLiteStorageManager",
    "ScraperReporter",
    "TerminalUI",
    "TokenBucketRateLimiter",
    "calculate_price_statistics",
    "export_all_formats",
    "export_to_csv",
    "export_to_markdown_table",
    "extract_book_detail",
    "generate_dashboard_html",
    "generate_full_analytics_summary",
    "normalize_book_record",
    "polite_get_with_retry",
    "process_and_validate_records",
    "save_records",
]
