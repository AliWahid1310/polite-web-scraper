"""
Scraper execution reporter module.
Collects runtime metrics, computes analytics summaries, and generates output/run-report.json.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from src.analytics import generate_full_analytics_summary


@dataclass
class RunMetrics:
    """Stores all metrics for a single scraping pipeline run."""
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    catalogue_pages_discovered: int = 0
    catalogue_pages_fetched: int = 0
    detail_pages_discovered: int = 0
    detail_pages_fetched: int = 0
    cache_hits: int = 0
    network_requests: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    failed_pages: int = 0
    failed_urls: list[dict] = field(default_factory=list)
    average_price_gbp: float = 0.0
    stock_total_units: int = 0
    analytics_summary: dict = field(default_factory=dict)


class ScraperReporter:
    """Manages tracking, aggregation, and disk persistence of run reports."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.metrics = RunMetrics()
        self._start_dt: datetime | None = None

    def start_run(self):
        """Mark start time of run."""
        self._start_dt = datetime.now(timezone.utc)
        self.metrics.start_time = self._start_dt.isoformat()

    def record_network_fetch(self, is_cache_hit: bool):
        """Record whether a request was served from cache or network."""
        if is_cache_hit:
            self.metrics.cache_hits += 1
        else:
            self.metrics.network_requests += 1

    def record_failure(self, url: str, reason: str, status_code: int | None = None):
        """Record a skipped or failed page."""
        self.metrics.failed_pages += 1
        self.metrics.failed_urls.append({
            "url": url,
            "reason": reason,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def finish_run(self, valid_records: list, error_records: list) -> dict:
        """Calculate final aggregates and persist output/run-report.json."""
        end_dt = datetime.now(timezone.utc)
        self.metrics.end_time = end_dt.isoformat()
        if self._start_dt:
            self.metrics.duration_seconds = round((end_dt - self._start_dt).total_seconds(), 2)

        self.metrics.valid_records = len(valid_records)
        self.metrics.invalid_records = len(error_records)

        # Statistical aggregates
        dict_records = []
        if valid_records:
            for r in valid_records:
                if hasattr(r, "model_dump"):
                    dict_records.append(r.model_dump())
                elif isinstance(r, dict):
                    dict_records.append(r)
                elif hasattr(r, "__dict__"):
                    dict_records.append(r.__dict__)

            prices = [r.get("price_gbp", 0.0) for r in dict_records if "price_gbp" in r]
            stocks = [r.get("stock_count", 0) for r in dict_records if "stock_count" in r]
            if prices:
                self.metrics.average_price_gbp = round(sum(prices) / len(prices), 2)
            if stocks:
                self.metrics.stock_total_units = sum(stocks)

            self.metrics.analytics_summary = generate_full_analytics_summary(dict_records)

        os.makedirs(self.output_dir, exist_ok=True)
        report_path = os.path.join(self.output_dir, "run-report.json")
        report_data = asdict(self.metrics)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return report_data
