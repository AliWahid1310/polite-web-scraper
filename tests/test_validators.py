"""Tests for custom validators and sanitizers (src/validators.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validators import RecordValidator, TextSanitizer, URLValidator


class TestURLValidator:
    """Test URL validation and normalization."""

    def test_valid_http_url(self):
        assert URLValidator.is_valid("https://books.toscrape.com/page-1.html") is True

    def test_valid_https_url(self):
        assert URLValidator.is_valid("https://example.com") is True

    def test_invalid_ftp_url(self):
        assert URLValidator.is_valid("ftp://example.com") is False

    def test_invalid_empty(self):
        assert URLValidator.is_valid("") is False

    def test_invalid_none(self):
        assert URLValidator.is_valid(None) is False

    def test_invalid_no_domain(self):
        assert URLValidator.is_valid("http://") is False

    def test_too_long_url(self):
        assert URLValidator.is_valid("https://example.com/" + "a" * 2050) is False

    def test_normalize_trailing_hash(self):
        assert URLValidator.normalize("https://example.com#") == "https://example.com"

    def test_normalize_whitespace(self):
        assert URLValidator.normalize("  https://example.com  ") == "https://example.com"

    def test_same_domain(self):
        assert URLValidator.is_same_domain("https://books.toscrape.com/page", "toscrape.com")

    def test_different_domain(self):
        assert not URLValidator.is_same_domain("https://other.com/page", "toscrape.com")

    def test_extract_domain(self):
        assert URLValidator.extract_domain("https://books.toscrape.com/path") == "books.toscrape.com"


class TestTextSanitizer:
    """Test text cleaning and sanitization."""

    def test_clean_whitespace(self):
        assert TextSanitizer.clean_whitespace("  hello   world  ") == "hello world"

    def test_clean_whitespace_empty(self):
        assert TextSanitizer.clean_whitespace("") == ""

    def test_remove_html_tags(self):
        assert TextSanitizer.remove_html_tags("<b>Bold</b> text") == "Bold text"

    def test_remove_nested_tags(self):
        assert TextSanitizer.remove_html_tags("<div><p>Hello</p></div>") == "Hello"

    def test_truncate_short_text(self):
        assert TextSanitizer.truncate("short", max_length=100) == "short"

    def test_truncate_long_text(self):
        result = TextSanitizer.truncate("a" * 100, max_length=20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_is_meaningful_true(self):
        assert TextSanitizer.is_meaningful("This is a good sentence") is True

    def test_is_meaningful_false(self):
        assert TextSanitizer.is_meaningful("OK") is False

    def test_is_meaningful_empty(self):
        assert TextSanitizer.is_meaningful("") is False


class TestRecordValidator:
    """Test record-level data quality validation."""

    def _valid_record(self):
        return {
            "title": "A Light in the Attic",
            "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
            "price_gbp": 51.77,
            "stock_count": 22,
            "rating": 3,
        }

    def test_valid_record_passes(self):
        issues = RecordValidator.validate_record(self._valid_record())
        assert issues == []

    def test_missing_title(self):
        rec = self._valid_record()
        del rec["title"]
        issues = RecordValidator.validate_record(rec)
        assert any("title" in i.lower() for i in issues)

    def test_empty_title(self):
        rec = self._valid_record()
        rec["title"] = "   "
        issues = RecordValidator.validate_record(rec)
        assert any("empty" in i.lower() for i in issues)

    def test_invalid_url(self):
        rec = self._valid_record()
        rec["product_url"] = "not-a-url"
        issues = RecordValidator.validate_record(rec)
        assert any("url" in i.lower() for i in issues)

    def test_negative_price(self):
        rec = self._valid_record()
        rec["price_gbp"] = -5.0
        issues = RecordValidator.validate_record(rec)
        assert any("positive" in i.lower() for i in issues)

    def test_extreme_price(self):
        rec = self._valid_record()
        rec["price_gbp"] = 99999.0
        issues = RecordValidator.validate_record(rec)
        assert any("high" in i.lower() for i in issues)

    def test_negative_stock(self):
        rec = self._valid_record()
        rec["stock_count"] = -1
        issues = RecordValidator.validate_record(rec)
        assert any("negative" in i.lower() for i in issues)

    def test_invalid_rating(self):
        rec = self._valid_record()
        rec["rating"] = 7
        issues = RecordValidator.validate_record(rec)
        assert any("1-5" in i for i in issues)

    def test_dataset_validation(self):
        records = [self._valid_record(), self._valid_record()]
        report = RecordValidator.validate_dataset(records)
        assert report["total_records"] == 2
        assert report["clean_records"] == 2
        assert report["quality_score_percent"] == 100.0

    def test_dataset_with_issues(self):
        good = self._valid_record()
        bad = {"title": "", "product_url": "bad", "price_gbp": -1}
        report = RecordValidator.validate_dataset([good, bad])
        assert report["records_with_issues"] == 1
        assert report["quality_score_percent"] == 50.0

    def test_duplicate_detection(self):
        rec = self._valid_record()
        report = RecordValidator.validate_dataset([rec, rec])
        assert report["duplicate_urls"] == 1
