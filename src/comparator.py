"""
Multi-Run Dataset Comparator and Change Tracker.
Compares two datasets (previous vs current scrape runs) to detect new records,
removed records, price changes, stock changes, and rating changes.
Useful for monitoring product catalogue evolution over time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DatasetComparator:
    """
    Compares two list[dict] datasets keyed by product_url and reports
    additions, removals, and field-level changes.
    """

    TRACKED_FIELDS = ["price_gbp", "stock_count", "rating", "availability_text", "title"]

    def __init__(
        self,
        previous: list[dict[str, Any]],
        current: list[dict[str, Any]],
        key_field: str = "product_url",
    ) -> None:
        self.previous = previous
        self.current = current
        self.key_field = key_field

    def _index_by_key(self, records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Build a lookup dict keyed by key_field."""
        index: dict[str, dict[str, Any]] = {}
        for rec in records:
            key = str(rec.get(self.key_field, ""))
            if key:
                index[key] = rec
        return index

    def compare(self) -> dict[str, Any]:
        """
        Run the full comparison and return a structured diff report.
        """
        prev_idx = self._index_by_key(self.previous)
        curr_idx = self._index_by_key(self.current)

        prev_keys = set(prev_idx.keys())
        curr_keys = set(curr_idx.keys())

        added_keys = curr_keys - prev_keys
        removed_keys = prev_keys - curr_keys
        common_keys = prev_keys & curr_keys

        # Detect field-level changes on common records
        changes: list[dict[str, Any]] = []
        for key in sorted(common_keys):
            prev_rec = prev_idx[key]
            curr_rec = curr_idx[key]
            field_changes = self._diff_record(prev_rec, curr_rec)
            if field_changes:
                changes.append({
                    "url": key,
                    "title": curr_rec.get("title", prev_rec.get("title", "")),
                    "changes": field_changes,
                })

        # Build added/removed summaries
        added = [
            {"url": k, "title": curr_idx[k].get("title", "")}
            for k in sorted(added_keys)
        ]
        removed = [
            {"url": k, "title": prev_idx[k].get("title", "")}
            for k in sorted(removed_keys)
        ]

        return {
            "comparison_timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_count": len(self.previous),
            "current_count": len(self.current),
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changes),
            "unchanged_count": len(common_keys) - len(changes),
            "added": added,
            "removed": removed,
            "changes": changes,
        }

    def _diff_record(
        self, prev: dict[str, Any], curr: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Compare two records and return a list of field-level diffs."""
        diffs: list[dict[str, Any]] = []
        for f in self.TRACKED_FIELDS:
            prev_val = prev.get(f)
            curr_val = curr.get(f)
            if prev_val != curr_val:
                diff_entry: dict[str, Any] = {
                    "field": f,
                    "previous": prev_val,
                    "current": curr_val,
                }
                # Add numeric delta for price and stock
                if f in ("price_gbp", "stock_count") and prev_val is not None and curr_val is not None:
                    try:
                        delta = float(curr_val) - float(prev_val)
                        diff_entry["delta"] = round(delta, 2)
                        if float(prev_val) != 0:
                            diff_entry["percent_change"] = round(
                                (delta / float(prev_val)) * 100, 2
                            )
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass
                diffs.append(diff_entry)
        return diffs

    def get_price_changes(self) -> list[dict[str, Any]]:
        """Extract only price-related changes from the comparison."""
        full_diff = self.compare()
        price_changes = []
        for change in full_diff.get("changes", []):
            price_diffs = [c for c in change["changes"] if c["field"] == "price_gbp"]
            if price_diffs:
                price_changes.append({
                    "url": change["url"],
                    "title": change["title"],
                    "price_change": price_diffs[0],
                })
        return price_changes

    def get_stock_changes(self) -> list[dict[str, Any]]:
        """Extract only stock-related changes from the comparison."""
        full_diff = self.compare()
        stock_changes = []
        for change in full_diff.get("changes", []):
            stock_diffs = [c for c in change["changes"] if c["field"] == "stock_count"]
            if stock_diffs:
                stock_changes.append({
                    "url": change["url"],
                    "title": change["title"],
                    "stock_change": stock_diffs[0],
                })
        return stock_changes

    @staticmethod
    def summarize(diff_report: dict[str, Any]) -> str:
        """Generate a human-readable text summary from a diff report."""
        lines = [
            "Dataset Comparison Summary",
            f"{'=' * 40}",
            f"Previous records: {diff_report['previous_count']}",
            f"Current records:  {diff_report['current_count']}",
            "",
            f"Added:     {diff_report['added_count']}",
            f"Removed:   {diff_report['removed_count']}",
            f"Changed:   {diff_report['changed_count']}",
            f"Unchanged: {diff_report['unchanged_count']}",
        ]

        if diff_report.get("added"):
            lines.append("\nNewly Added:")
            for item in diff_report["added"][:10]:
                lines.append(f"  + {item['title']}")

        if diff_report.get("removed"):
            lines.append("\nRemoved:")
            for item in diff_report["removed"][:10]:
                lines.append(f"  - {item['title']}")

        if diff_report.get("changes"):
            lines.append("\nChanged Records:")
            for item in diff_report["changes"][:10]:
                lines.append(f"  ~ {item['title']}")
                for c in item["changes"]:
                    delta_str = ""
                    if "delta" in c:
                        sign = "+" if c["delta"] >= 0 else ""
                        delta_str = f" ({sign}{c['delta']})"
                    lines.append(
                        f"    {c['field']}: {c['previous']} → {c['current']}{delta_str}"
                    )

        return "\n".join(lines)
