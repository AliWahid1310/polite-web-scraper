"""
Polite Web Scraper package.
A robust, respectful, production-grade scraping pipeline for Books to Scrape.
"""

from __future__ import annotations

__version__ = "2.1.0"
__author__ = "AliWahid1310"

from src.analytics import calculate_price_statistics, generate_full_analytics_summary
from src.audit import DatasetAuditor
from src.cache_manager import CacheManager, CacheStats
from src.comparator import DatasetComparator
from src.config import ScraperConfig, get_config, reset_config
from src.dashboard import generate_dashboard_html
from src.exporters import export_all_formats, export_to_csv, export_to_markdown_table
from src.extract import extract_book_detail
from src.headers import RespectfulHeaderManager
from src.normalizer import normalize_book_record
from src.notifications import EventLevel, EventType, NotificationManager, PipelineEvent
from src.rate_limiter import TokenBucketRateLimiter
from src.reporter import ScraperReporter
from src.retry import polite_get_with_retry
from src.schemas import BookRecord, ErrorRecord
from src.sqlite_storage import SQLiteStorageManager
from src.storage import process_and_validate_records, save_records
from src.terminal_ui import TerminalUI
from src.validators import RecordValidator, TextSanitizer, URLValidator

__all__ = [
    "BookRecord",
    "CacheManager",
    "CacheStats",
    "DatasetAuditor",
    "DatasetComparator",
    "ErrorRecord",
    "EventLevel",
    "EventType",
    "NotificationManager",
    "PipelineEvent",
    "RecordValidator",
    "RespectfulHeaderManager",
    "SQLiteStorageManager",
    "ScraperConfig",
    "ScraperReporter",
    "TerminalUI",
    "TextSanitizer",
    "TokenBucketRateLimiter",
    "URLValidator",
    "calculate_price_statistics",
    "export_all_formats",
    "export_to_csv",
    "export_to_markdown_table",
    "extract_book_detail",
    "generate_dashboard_html",
    "generate_full_analytics_summary",
    "get_config",
    "normalize_book_record",
    "polite_get_with_retry",
    "process_and_validate_records",
    "reset_config",
    "save_records",
]
