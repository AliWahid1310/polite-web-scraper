"""
Advanced Cache Manager with TTL, Statistics, and Eviction Policies.
Extends the basic file-based caching in the pipeline with lifecycle tracking,
time-based expiration, size limits, and cache performance analytics.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheStats:
    """Runtime statistics for cache performance monitoring."""
    total_lookups: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    writes: int = 0
    bytes_read: int = 0
    bytes_written: int = 0

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a percentage (0-100)."""
        if self.total_lookups == 0:
            return 0.0
        return round((self.hits / self.total_lookups) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_lookups": self.total_lookups,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "writes": self.writes,
            "bytes_read": self.bytes_read,
            "bytes_written": self.bytes_written,
            "hit_rate_percent": self.hit_rate,
        }


class CacheManager:
    """
    Advanced file-based HTTP cache with TTL enforcement, size budgets,
    and observability metrics.
    """

    def __init__(
        self,
        cache_dir: str = "cache",
        ttl_seconds: int = 86400,
        max_entries: int = 10000,
    ) -> None:
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.stats = CacheStats()

    def _url_to_path(self, url: str) -> str:
        """Convert a URL to a filesystem-safe cache file path."""
        safe = re.sub(r"[^a-zA-Z0-9]", "_", url)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        filename = f"{safe[:80]}_{url_hash}.html"
        return os.path.join(self.cache_dir, filename)

    def _is_expired(self, file_path: str) -> bool:
        """Check if a cached file has exceeded the configured TTL."""
        if self.ttl_seconds <= 0:
            return False  # TTL disabled
        try:
            mtime = os.path.getmtime(file_path)
            age = time.time() - mtime
            return age > self.ttl_seconds
        except OSError:
            return True

    def get(self, url: str) -> str | None:
        """
        Retrieve cached content for a URL.
        Returns None on miss or expiration.
        """
        self.stats.total_lookups += 1
        path = self._url_to_path(url)

        if not os.path.exists(path):
            self.stats.misses += 1
            return None

        if self._is_expired(path):
            self.stats.misses += 1
            self._remove_file(path)
            self.stats.evictions += 1
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.stats.hits += 1
            self.stats.bytes_read += len(content.encode("utf-8"))
            return content
        except (OSError, UnicodeDecodeError):
            self.stats.misses += 1
            return None

    def put(self, url: str, content: str) -> str:
        """
        Store content in the cache for the given URL.
        Enforces max_entries by evicting oldest files if capacity is exceeded.
        Returns the cache file path.
        """
        os.makedirs(self.cache_dir, exist_ok=True)

        # Enforce size limit before writing
        self._enforce_max_entries()

        path = self._url_to_path(url)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        self.stats.writes += 1
        self.stats.bytes_written += len(content.encode("utf-8"))
        return path

    def has(self, url: str) -> bool:
        """Check if a non-expired cache entry exists for the given URL."""
        path = self._url_to_path(url)
        if not os.path.exists(path):
            return False
        if self._is_expired(path):
            self._remove_file(path)
            self.stats.evictions += 1
            return False
        return True

    def invalidate(self, url: str) -> bool:
        """Remove a specific URL's cache entry. Returns True if removed."""
        path = self._url_to_path(url)
        return self._remove_file(path)

    def clear(self) -> int:
        """
        Clear all cached files in the cache directory.
        Returns the number of entries removed.
        """
        removed = 0
        if not os.path.isdir(self.cache_dir):
            return 0
        for fname in os.listdir(self.cache_dir):
            fpath = os.path.join(self.cache_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".html"):
                self._remove_file(fpath)
                removed += 1
        self.stats.evictions += removed
        return removed

    def get_entry_count(self) -> int:
        """Count the number of HTML cache entries on disk."""
        if not os.path.isdir(self.cache_dir):
            return 0
        return sum(
            1 for f in os.listdir(self.cache_dir)
            if f.endswith(".html") and os.path.isfile(os.path.join(self.cache_dir, f))
        )

    def get_total_size_bytes(self) -> int:
        """Calculate total size of all cached files in bytes."""
        if not os.path.isdir(self.cache_dir):
            return 0
        total = 0
        for fname in os.listdir(self.cache_dir):
            fpath = os.path.join(self.cache_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".html"):
                total += os.path.getsize(fpath)
        return total

    def evict_expired(self) -> int:
        """Scan and remove all expired cache entries. Returns count of evicted entries."""
        evicted = 0
        if not os.path.isdir(self.cache_dir):
            return 0
        for fname in os.listdir(self.cache_dir):
            fpath = os.path.join(self.cache_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".html"):
                if self._is_expired(fpath):
                    self._remove_file(fpath)
                    evicted += 1
        self.stats.evictions += evicted
        return evicted

    def get_cache_summary(self) -> dict[str, Any]:
        """Return a comprehensive cache state summary."""
        entry_count = self.get_entry_count()
        total_bytes = self.get_total_size_bytes()
        return {
            "cache_dir": self.cache_dir,
            "ttl_seconds": self.ttl_seconds,
            "max_entries": self.max_entries,
            "current_entries": entry_count,
            "total_size_bytes": total_bytes,
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "utilization_percent": round((entry_count / self.max_entries) * 100, 2) if self.max_entries > 0 else 0.0,
            "stats": self.stats.to_dict(),
        }

    def _enforce_max_entries(self) -> None:
        """Evict oldest entries if cache exceeds max_entries."""
        if self.max_entries <= 0:
            return

        entries = self._list_entries_by_age()
        excess = len(entries) - self.max_entries + 1  # Make room for 1 new entry

        if excess > 0:
            for path, _ in entries[:excess]:
                self._remove_file(path)
                self.stats.evictions += 1

    def _list_entries_by_age(self) -> list[tuple[str, float]]:
        """List cache entries sorted by modification time (oldest first)."""
        if not os.path.isdir(self.cache_dir):
            return []
        entries = []
        for fname in os.listdir(self.cache_dir):
            fpath = os.path.join(self.cache_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".html"):
                try:
                    mtime = os.path.getmtime(fpath)
                    entries.append((fpath, mtime))
                except OSError:
                    continue
        entries.sort(key=lambda x: x[1])
        return entries

    @staticmethod
    def _remove_file(path: str) -> bool:
        """Safely remove a file. Returns True if removed."""
        try:
            os.remove(path)
            return True
        except OSError:
            return False
