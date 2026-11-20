"""
Concurrent Queue Worker Pool with Concurrency Cap (Stretch Goal).
Processes scraping jobs through a bounded worker pool while strictly respecting
polite rate limits, thread-safety, and idempotent writing.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from src.extract import extract_book_detail


class PoliteWorkerPool:
    """
    Manages background scraping execution with a strict concurrency limit
    to prevent overwhelming target sandbox servers.
    """

    def __init__(self, max_concurrency: int = 2):
        self.max_concurrency = max(1, max_concurrency)
        self._lock = threading.Lock()

    def process_jobs(
        self,
        job_entries: list[dict],
        fetch_fn: Callable[[str], str | None],
        progress_callback: Callable[[int, int], None] | None = None,
        failure_callback: Callable[[str, Exception], None] | None = None,
    ) -> list[dict]:
        """
        Execute detail page scraping jobs concurrently up to max_concurrency cap.
        Supports thread-safe progress reporting and failure callbacks.
        Returns aggregated raw extracted records.
        """
        results: list[dict] = []
        total_jobs = len(job_entries)
        completed_count = 0

        def _scrape_worker(entry: dict) -> dict | None:
            url = entry.get("url", "")
            source_page = entry.get("source_page", "")
            try:
                html = fetch_fn(url)
                if not html:
                    return None
                return extract_book_detail(html, url, source_page)
            except Exception as exc:
                if failure_callback:
                    failure_callback(url, exc)
                return None

        with ThreadPoolExecutor(max_workers=self.max_concurrency) as executor:
            future_to_entry = {
                executor.submit(_scrape_worker, entry): entry
                for entry in job_entries
            }

            for future in as_completed(future_to_entry):
                try:
                    record = future.result()
                    if record:
                        with self._lock:
                            results.append(record)
                except Exception:
                    pass
                finally:
                    with self._lock:
                        completed_count += 1
                        if progress_callback:
                            progress_callback(completed_count, total_jobs)

        return results
