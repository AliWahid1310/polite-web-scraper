"""
Export utility module.
Produces clean exports in CSV, Markdown Table, NDJSON, and XML formats
from schema-validated BookRecords.
"""

from __future__ import annotations

import csv
import html
import json
import os
from typing import Any


def _to_dict(rec: Any) -> dict[str, Any]:
    """Helper to convert BookRecord or dict to plain dict."""
    if hasattr(rec, "model_dump"):
        return rec.model_dump()
    if isinstance(rec, dict):
        return rec
    if hasattr(rec, "__dict__"):
        return rec.__dict__
    return dict(rec)


def export_to_csv(records: list[Any], output_path: str = "output/books.csv") -> str:
    """
    Export validated records into a standard CSV format.
    Flattens HttpUrl, datetime, and multiline descriptions for clean tabular consumption.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fieldnames = [
        "title",
        "product_url",
        "price_gbp",
        "price_text",
        "stock_count",
        "is_in_stock",
        "availability_text",
        "rating",
        "rating_text",
        "total_inventory_value_gbp",
        "description",
        "source_page",
        "fetched_at",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for raw_item in records:
            d = _to_dict(raw_item)
            desc = d.get("description") or ""
            desc_clean = " ".join(desc.split())

            writer.writerow({
                "title": d.get("title", ""),
                "product_url": str(d.get("product_url", "")),
                "price_gbp": d.get("price_gbp", 0.0),
                "price_text": d.get("price_text", ""),
                "stock_count": d.get("stock_count", 0),
                "is_in_stock": d.get("is_in_stock", True),
                "availability_text": d.get("availability_text", ""),
                "rating": d.get("rating", 0),
                "rating_text": d.get("rating_text", ""),
                "total_inventory_value_gbp": d.get("total_inventory_value_gbp", 0.0),
                "description": desc_clean,
                "source_page": str(d.get("source_page", "")),
                "fetched_at": str(d.get("fetched_at", "")),
            })

    return output_path


def export_to_markdown_table(records: list[Any], output_path: str = "output/books.md") -> str:
    """Export validated records as a GitHub-flavored Markdown table."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    lines = [
        "# Scraped Books Catalogue",
        "",
        f"Total Books: **{len(records)}**",
        "",
        "| # | Title | Price (GBP) | Rating | Stock | Available Units |",
        "|---|---|---|---|---|---|",
    ]

    for idx, raw_item in enumerate(records, 1):
        d = _to_dict(raw_item)
        title = d.get("title", "").replace("|", "-")
        url = d.get("product_url", "")
        price = f"£{float(d.get('price_gbp', 0.0)):.2f}"
        rating_num = int(d.get("rating", 0))
        stars = "★" * rating_num + "☆" * (5 - rating_num)
        stock_status = "In Stock" if d.get("stock_count", 0) > 0 else "Out of Stock"
        units = d.get("stock_count", 0)

        title_link = f"[{title}]({url})" if url else title
        lines.append(f"| {idx} | {title_link} | {price} | {stars} ({rating_num}) | {stock_status} | {units} |")

    lines.append("")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def export_to_ndjson(records: list[Any], output_path: str = "output/books.ndjson") -> str:
    """Export validated records to Newline Delimited JSON (NDJSON) for streaming pipelines."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for raw_item in records:
            d = _to_dict(raw_item)
            # Ensure datetime or HttpUrl are JSON serializable
            serialized = json.dumps(d, ensure_ascii=False, default=str)
            f.write(serialized + "\n")

    return output_path


def export_to_xml(records: list[Any], output_path: str = "output/books.xml") -> str:
    """Export validated records as clean structured XML."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<catalogue source="Books to Scrape">',
    ]

    for raw_item in records:
        d = _to_dict(raw_item)
        xml_lines.append("  <book>")
        for key, val in d.items():
            str_val = html.escape(str(val) if val is not None else "")
            xml_lines.append(f"    <{key}>{str_val}</{key}>")
        xml_lines.append("  </book>")

    xml_lines.append("</catalogue>")
    xml_lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))

    return output_path


def export_all_formats(records: list[Any], base_dir: str = "output") -> dict[str, str]:
    """Convenience helper to export records in all available formats."""
    return {
        "csv": export_to_csv(records, os.path.join(base_dir, "books.csv")),
        "markdown": export_to_markdown_table(records, os.path.join(base_dir, "books.md")),
        "ndjson": export_to_ndjson(records, os.path.join(base_dir, "books.ndjson")),
        "xml": export_to_xml(records, os.path.join(base_dir, "books.xml")),
    }
