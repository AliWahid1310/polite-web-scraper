"""
Dataset Integrity Auditor & Cryptographic Manifest Generator.
Verifies record schema adherence, detects anomalies, checks for duplicates,
and produces verifiable SHA-256 audit manifests for data governance.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any


class DatasetAuditor:
    """
    Validates dataset integrity, checks for semantic inconsistencies,
    and generates verifiable SHA-256 integrity digests.
    """

    @staticmethod
    def compute_record_digest(record: dict[str, Any]) -> str:
        """Compute deterministic SHA-256 hash of a normalized record dictionary."""
        serialized = json.dumps(record, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def verify_records_integrity(cls, records: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Verify integrity across a list of book records:
        - Check for duplicate URLs and titles
        - Identify missing fields or zero values
        - Compute dataset Merkle-like root hash
        """
        seen_urls: set[str] = set()
        duplicate_urls: list[str] = []
        seen_titles: set[str] = set()
        duplicate_titles: list[str] = []
        anomalies: list[dict[str, Any]] = []
        record_hashes: list[str] = []

        for idx, rec in enumerate(records):
            url = str(rec.get("product_url", "")).strip()
            title = str(rec.get("title", "")).strip()
            price = float(rec.get("price_gbp", 0.0))
            rating = int(rec.get("rating", 0))
            stock = int(rec.get("stock_count", 0))

            if url in seen_urls:
                duplicate_urls.append(url)
            else:
                seen_urls.add(url)

            if title in seen_titles:
                duplicate_titles.append(title)
            else:
                seen_titles.add(title)

            # Anomaly checks
            record_issues = []
            if price <= 0.0:
                record_issues.append("Non-positive price")
            if rating < 1 or rating > 5:
                record_issues.append(f"Rating {rating} outside valid [1, 5] range")
            if not title:
                record_issues.append("Missing or empty title")
            if not url:
                record_issues.append("Missing product URL")

            if record_issues:
                anomalies.append({
                    "record_index": idx,
                    "title": title or "Unknown",
                    "issues": record_issues,
                })

            record_hashes.append(cls.compute_record_digest(rec))

        # Combined root digest
        combined_payload = "".join(record_hashes)
        dataset_root_hash = (
            hashlib.sha256(combined_payload.encode("utf-8")).hexdigest()
            if record_hashes
            else hashlib.sha256(b"empty").hexdigest()
        )

        return {
            "total_records_checked": len(records),
            "unique_urls": len(seen_urls),
            "duplicate_url_count": len(duplicate_urls),
            "duplicate_urls": duplicate_urls,
            "duplicate_title_count": len(duplicate_titles),
            "duplicate_titles": duplicate_titles,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "dataset_root_hash": dataset_root_hash,
            "is_valid": len(duplicate_urls) == 0 and len(anomalies) == 0,
        }

    @classmethod
    def generate_audit_manifest(
        cls,
        records: list[dict[str, Any]],
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Generate comprehensive audit manifest with metadata and checksums."""
        audit_result = cls.verify_records_integrity(records)
        manifest = {
            "manifest_version": "2.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_dataset": "Books to Scrape (https://books.toscrape.com)",
            "record_count": len(records),
            "dataset_root_hash": audit_result["dataset_root_hash"],
            "verification_status": "PASSED" if audit_result["is_valid"] else "WARNING",
            "integrity_summary": {
                "unique_urls": audit_result["unique_urls"],
                "duplicates_detected": audit_result["duplicate_url_count"],
                "anomalies_detected": audit_result["anomaly_count"],
            },
        }

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

        return manifest
