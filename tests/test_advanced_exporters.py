"""
Unit tests for multi-format exporters (src/exporters.py).
"""

import json

from src.exporters import (
    export_all_formats,
    export_to_csv,
    export_to_markdown_table,
    export_to_ndjson,
    export_to_xml,
)


def _sample_records():
    return [
        {
            "title": "A Light in the Attic",
            "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
            "price_gbp": 51.77,
            "price_text": "£51.77",
            "currency": "GBP",
            "stock_count": 22,
            "is_in_stock": True,
            "availability_text": "In stock (22 available)",
            "rating": 3,
            "rating_text": "Three",
            "description": "It's hard to describe Shel Silverstein's poems.",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "total_inventory_value_gbp": 1138.94,
            "fetched_at": "2026-11-16T12:00:00Z",
        },
        {
            "title": "Tipping the Velvet",
            "product_url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
            "price_gbp": 53.74,
            "price_text": "£53.74",
            "currency": "GBP",
            "stock_count": 0,
            "is_in_stock": False,
            "availability_text": "Out of stock",
            "rating": 1,
            "rating_text": "One",
            "description": "Nan King, an oyster girl, is captivated by the music hall.",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "total_inventory_value_gbp": 0.0,
            "fetched_at": "2026-11-16T12:00:00Z",
        },
    ]


def test_export_to_markdown_table(tmp_path):
    records = _sample_records()
    out_file = tmp_path / "books.md"
    export_to_markdown_table(records, str(out_file))

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "# Scraped Books Catalogue" in content
    assert "| A Light in the Attic |" in content or "[A Light in the Attic]" in content
    assert "£51.77" in content
    assert "★★★☆☆" in content
    assert "★☆☆☆☆" in content
    assert "Out of Stock" in content


def test_export_to_ndjson(tmp_path):
    records = _sample_records()
    out_file = tmp_path / "books.ndjson"
    export_to_ndjson(records, str(out_file))

    assert out_file.exists()
    lines = out_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    row0 = json.loads(lines[0])
    assert row0["title"] == "A Light in the Attic"
    assert row0["price_gbp"] == 51.77


def test_export_to_xml(tmp_path):
    records = _sample_records()
    out_file = tmp_path / "books.xml"
    export_to_xml(records, str(out_file))

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<catalogue" in content
    assert "<book>" in content
    assert "<title>A Light in the Attic</title>" in content
    assert "<price_gbp>51.77</price_gbp>" in content
    assert "</catalogue>" in content


def test_export_all_formats(tmp_path):
    records = _sample_records()
    result = export_all_formats(records, str(tmp_path))

    assert "csv" in result
    assert "markdown" in result
    assert "ndjson" in result
    assert "xml" in result
    for key, path in result.items():
        assert (tmp_path / f"books.{'md' if key == 'markdown' else key}").exists()
