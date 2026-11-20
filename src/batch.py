"""
Batch Scraping & Targeted Filtering Manager.
Filters discovered target URLs by keyword, limits batches by price bounds,
or loads explicit target lists from external text/JSON manifest files.
"""

from __future__ import annotations

import json
import os
from typing import Any


class BatchScrapingManager:
    """Manages batching, filtering, and target subset selection."""

    @staticmethod
    def filter_by_keyword(entries: list[dict[str, Any]], keyword: str) -> list[dict[str, Any]]:
        """Filter catalogue entries whose URL or title slug contains keyword."""
        if not keyword:
            return entries
        k = keyword.lower().strip()
        return [
            e for e in entries
            if k in str(e.get("url", "")).lower() or k in str(e.get("title", "")).lower()
        ]

    @staticmethod
    def filter_by_price_bounds(
        records: list[dict[str, Any]],
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[dict[str, Any]]:
        """Filter extracted records within numeric price bounds."""
        results = records
        if min_price is not None:
            results = [r for r in results if float(r.get("price_gbp", 0.0)) >= min_price]
        if max_price is not None:
            results = [r for r in results if float(r.get("price_gbp", 0.0)) <= max_price]
        return results

    @staticmethod
    def load_targets_from_file(file_path: str) -> list[dict[str, str]]:
        """
        Load custom URLs from a plain text list (1 URL per line) or JSON file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target list not found: {file_path}")

        entries = []
        if file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            entries.append({"url": item.strip(), "source_page": "custom_batch"})
                        elif isinstance(item, dict) and "url" in item:
                            entries.append(item)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    u = line.strip()
                    if u and not u.startswith("#"):
                        entries.append({"url": u, "source_page": "custom_batch"})

        return entries
