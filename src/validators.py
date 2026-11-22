"""
Custom Data Validators and Sanitizers.
Provides URL validation, HTML content sanitization, field-level data quality checks,
and comprehensive record integrity verification for scraped data.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


class URLValidator:
    """Validates and normalizes URLs for safe scraping."""

    ALLOWED_SCHEMES = {"http", "https"}
    MAX_URL_LENGTH = 2048

    @classmethod
    def is_valid(cls, url: str) -> bool:
        """Check if a URL is valid for scraping."""
        if not url or not isinstance(url, str):
            return False
        if len(url) > cls.MAX_URL_LENGTH:
            return False
        try:
            parsed = urlparse(url.strip())
            return (
                parsed.scheme in cls.ALLOWED_SCHEMES
                and bool(parsed.netloc)
                and "." in parsed.netloc
            )
        except Exception:
            return False

    @classmethod
    def normalize(cls, url: str) -> str:
        """Normalize a URL by stripping whitespace and trailing fragments."""
        url = url.strip()
        # Remove trailing hash fragment if empty
        if url.endswith("#"):
            url = url[:-1]
        return url

    @classmethod
    def is_same_domain(cls, url: str, domain: str) -> bool:
        """Check if URL belongs to the specified domain."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().endswith(domain.lower())
        except Exception:
            return False

    @classmethod
    def extract_domain(cls, url: str) -> str:
        """Extract the domain from a URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""


class TextSanitizer:
    """Sanitizes and cleans text extracted from HTML."""

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Normalize all whitespace to single spaces and strip."""
        if not text:
            return ""
        return " ".join(text.split()).strip()

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """Remove any residual HTML tags from text."""
        if not text:
            return ""
        return re.sub(r"<[^>]+>", "", text).strip()

    @staticmethod
    def truncate(text: str, max_length: int = 500, suffix: str = "...") -> str:
        """Truncate text to max_length, appending suffix if truncated."""
        if not text or len(text) <= max_length:
            return text or ""
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def is_meaningful(text: str, min_words: int = 3) -> bool:
        """Check if text has enough meaningful content (not just noise)."""
        if not text:
            return False
        words = text.split()
        return len(words) >= min_words


class RecordValidator:
    """Validates individual scraped book records for data quality."""

    REQUIRED_FIELDS = ["title", "product_url", "price_gbp", "stock_count", "rating"]

    @classmethod
    def validate_record(cls, record: dict[str, Any]) -> list[str]:
        """
        Validate a single record and return a list of issues.
        Returns empty list if record passes all checks.
        """
        issues: list[str] = []

        # Check required fields
        for f in cls.REQUIRED_FIELDS:
            if f not in record or record[f] is None:
                issues.append(f"Missing required field: {f}")

        # Validate title
        title = record.get("title", "")
        if isinstance(title, str):
            if not title.strip():
                issues.append("Title is empty or whitespace-only")
            elif len(title) > 500:
                issues.append(f"Title too long ({len(title)} chars, max 500)")

        # Validate URL
        url = record.get("product_url", "")
        if isinstance(url, str) and not URLValidator.is_valid(url):
            issues.append(f"Invalid product URL: {url[:80]}...")

        # Validate price
        price = record.get("price_gbp")
        if price is not None:
            try:
                p = float(price)
                if p <= 0:
                    issues.append(f"Price must be positive, got {p}")
                elif p > 10000:
                    issues.append(f"Price seems unreasonably high: {p}")
            except (TypeError, ValueError):
                issues.append(f"Price is not a valid number: {price}")

        # Validate stock count
        stock = record.get("stock_count")
        if stock is not None:
            try:
                s = int(stock)
                if s < 0:
                    issues.append(f"Stock count cannot be negative: {s}")
                elif s > 100000:
                    issues.append(f"Stock count unreasonably high: {s}")
            except (TypeError, ValueError):
                issues.append(f"Stock count is not a valid integer: {stock}")

        # Validate rating
        rating = record.get("rating")
        if rating is not None:
            try:
                r = int(rating)
                if r < 1 or r > 5:
                    issues.append(f"Rating must be 1-5, got {r}")
            except (TypeError, ValueError):
                issues.append(f"Rating is not a valid integer: {rating}")

        return issues

    @classmethod
    def validate_dataset(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate an entire dataset and return a quality report.
        """
        total = len(records)
        clean_count = 0
        issue_count = 0
        all_issues: list[dict[str, Any]] = []

        for idx, rec in enumerate(records):
            issues = cls.validate_record(rec)
            if issues:
                issue_count += 1
                all_issues.append({
                    "index": idx,
                    "title": rec.get("title", "UNKNOWN"),
                    "issues": issues,
                })
            else:
                clean_count += 1

        # Check for duplicates
        urls = [str(r.get("product_url", "")) for r in records]
        unique_urls = set(urls)
        duplicates = total - len(unique_urls) if total > len(unique_urls) else 0

        return {
            "total_records": total,
            "clean_records": clean_count,
            "records_with_issues": issue_count,
            "duplicate_urls": duplicates,
            "quality_score_percent": round((clean_count / total) * 100, 1) if total > 0 else 0.0,
            "issues": all_issues[:50],  # Limit detail output
        }
