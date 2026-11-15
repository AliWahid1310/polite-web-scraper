"""
Unit tests for Dataset Integrity Auditor & Manifest Generator (src/audit.py).
"""

import json

from src.audit import DatasetAuditor


def test_compute_record_digest():
    record1 = {"title": "Test Book", "price_gbp": 12.99, "product_url": "https://example.com/1"}
    record2 = {"product_url": "https://example.com/1", "price_gbp": 12.99, "title": "Test Book"}
    # Digest should be deterministic regardless of dictionary key insertion order
    h1 = DatasetAuditor.compute_record_digest(record1)
    h2 = DatasetAuditor.compute_record_digest(record2)
    assert h1 == h2
    assert len(h1) == 64


def test_verify_records_integrity_valid():
    records = [
        {"title": "Book A", "product_url": "https://books.toscrape.com/a", "price_gbp": 10.0, "rating": 3, "stock_count": 5},
        {"title": "Book B", "product_url": "https://books.toscrape.com/b", "price_gbp": 15.0, "rating": 5, "stock_count": 2},
    ]
    res = DatasetAuditor.verify_records_integrity(records)
    assert res["is_valid"] is True
    assert res["total_records_checked"] == 2
    assert res["unique_urls"] == 2
    assert res["duplicate_url_count"] == 0
    assert res["anomaly_count"] == 0
    assert res["dataset_root_hash"] is not None


def test_verify_records_integrity_duplicates_and_anomalies():
    records = [
        {"title": "Book A", "product_url": "https://books.toscrape.com/a", "price_gbp": 10.0, "rating": 3, "stock_count": 5},
        # Duplicate URL:
        {"title": "Book A Duplicate", "product_url": "https://books.toscrape.com/a", "price_gbp": 10.0, "rating": 3, "stock_count": 5},
        # Anomalies: zero price, out-of-range rating:
        {"title": "Anomalous Book", "product_url": "https://books.toscrape.com/c", "price_gbp": -5.0, "rating": 9, "stock_count": 0},
    ]
    res = DatasetAuditor.verify_records_integrity(records)
    assert res["is_valid"] is False
    assert res["duplicate_url_count"] == 1
    assert "https://books.toscrape.com/a" in res["duplicate_urls"]
    assert res["anomaly_count"] == 1
    issues = res["anomalies"][0]["issues"]
    assert "Non-positive price" in issues
    assert "Rating 9 outside valid [1, 5] range" in issues


def test_generate_audit_manifest(tmp_path):
    records = [
        {"title": "Book A", "product_url": "https://books.toscrape.com/a", "price_gbp": 10.0, "rating": 4, "stock_count": 3}
    ]
    out_file = tmp_path / "manifest.json"
    manifest = DatasetAuditor.generate_audit_manifest(records, output_path=str(out_file))

    assert manifest["manifest_version"] == "2.0.0"
    assert manifest["verification_status"] == "PASSED"
    assert manifest["record_count"] == 1
    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["dataset_root_hash"] == manifest["dataset_root_hash"]
