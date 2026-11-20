"""
Unit tests for Batch Scraping & Filtering Manager (src/batch.py).
"""

import json

import pytest

from src.batch import BatchScrapingManager


def test_filter_by_keyword():
    entries = [
        {"url": "https://books.toscrape.com/catalogue/poetry-in-motion/index.html", "title": "Poetry in Motion"},
        {"url": "https://books.toscrape.com/catalogue/cooking-101/index.html", "title": "Cooking 101"},
    ]
    filtered = BatchScrapingManager.filter_by_keyword(entries, "poetry")
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Poetry in Motion"

    # Empty keyword returns all
    assert len(BatchScrapingManager.filter_by_keyword(entries, "")) == 2


def test_filter_by_price_bounds():
    records = [
        {"title": "Cheap Book", "price_gbp": 12.0},
        {"title": "Mid Book", "price_gbp": 35.0},
        {"title": "Expensive Book", "price_gbp": 85.0},
    ]
    bounded = BatchScrapingManager.filter_by_price_bounds(records, min_price=20.0, max_price=50.0)
    assert len(bounded) == 1
    assert bounded[0]["title"] == "Mid Book"


def test_load_targets_from_text_file(tmp_path):
    target_file = tmp_path / "targets.txt"
    target_file.write_text(
        "# Comment line\nhttps://books.toscrape.com/1\nhttps://books.toscrape.com/2\n",
        encoding="utf-8",
    )
    targets = BatchScrapingManager.load_targets_from_file(str(target_file))
    assert len(targets) == 2
    assert targets[0]["url"] == "https://books.toscrape.com/1"


def test_load_targets_from_json_file(tmp_path):
    target_file = tmp_path / "targets.json"
    target_file.write_text(
        json.dumps(["https://books.toscrape.com/a", "https://books.toscrape.com/b"]),
        encoding="utf-8",
    )
    targets = BatchScrapingManager.load_targets_from_file(str(target_file))
    assert len(targets) == 2
    assert targets[0]["url"] == "https://books.toscrape.com/a"


def test_load_targets_missing_file():
    with pytest.raises(FileNotFoundError):
        BatchScrapingManager.load_targets_from_file("nonexistent_file_path.txt")
