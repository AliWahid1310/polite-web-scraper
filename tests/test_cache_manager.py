"""Tests for the advanced cache manager (src/cache_manager.py)."""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache_manager import CacheManager, CacheStats


class TestCacheStats:
    """Test CacheStats dataclass."""

    def test_initial_stats(self):
        stats = CacheStats()
        assert stats.total_lookups == 0
        assert stats.hits == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        stats = CacheStats(total_lookups=10, hits=7, misses=3)
        assert stats.hit_rate == 70.0

    def test_to_dict(self):
        stats = CacheStats(total_lookups=5, hits=3, misses=2, writes=5)
        d = stats.to_dict()
        assert d["total_lookups"] == 5
        assert d["hit_rate_percent"] == 60.0


class TestCacheManager:
    """Test CacheManager operations."""

    def test_put_and_get(self, tmp_path):
        """Should store and retrieve content correctly."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        url = "https://example.com/page1"
        cm.put(url, "<html>Hello</html>")
        result = cm.get(url)
        assert result == "<html>Hello</html>"
        assert cm.stats.writes == 1
        assert cm.stats.hits == 1

    def test_cache_miss(self, tmp_path):
        """Should return None for uncached URLs."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        result = cm.get("https://example.com/nonexistent")
        assert result is None
        assert cm.stats.misses == 1

    def test_has_method(self, tmp_path):
        """has() should return True for existing, non-expired entries."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        url = "https://example.com/check"
        assert cm.has(url) is False
        cm.put(url, "content")
        assert cm.has(url) is True

    def test_invalidate(self, tmp_path):
        """invalidate() should remove a specific cache entry."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        url = "https://example.com/remove"
        cm.put(url, "data")
        assert cm.has(url)
        cm.invalidate(url)
        assert not cm.has(url)

    def test_clear_all(self, tmp_path):
        """clear() should remove all entries."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        cm.put("https://example.com/a", "a")
        cm.put("https://example.com/b", "b")
        assert cm.get_entry_count() == 2
        removed = cm.clear()
        assert removed == 2
        assert cm.get_entry_count() == 0

    def test_entry_count(self, tmp_path):
        """get_entry_count() should count cached files accurately."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        assert cm.get_entry_count() == 0
        cm.put("https://example.com/1", "one")
        cm.put("https://example.com/2", "two")
        assert cm.get_entry_count() == 2

    def test_total_size_bytes(self, tmp_path):
        """get_total_size_bytes() should return cumulative byte size."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        cm.put("https://example.com/size", "Hello World")
        size = cm.get_total_size_bytes()
        assert size > 0

    def test_cache_summary(self, tmp_path):
        """get_cache_summary() should return a comprehensive report dict."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"), ttl_seconds=3600)
        cm.put("https://example.com/sum", "data")
        cm.get("https://example.com/sum")
        summary = cm.get_cache_summary()
        assert summary["current_entries"] == 1
        assert summary["ttl_seconds"] == 3600
        assert "stats" in summary
        assert summary["stats"]["hits"] == 1

    def test_ttl_expiration(self, tmp_path):
        """Expired entries should return None and be evicted."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"), ttl_seconds=1)
        url = "https://example.com/ttl"
        path = cm.put(url, "temporary")
        # Backdate the file to make it expired
        old_time = time.time() - 10
        os.utime(path, (old_time, old_time))
        result = cm.get(url)
        assert result is None
        assert cm.stats.evictions >= 1

    def test_max_entries_eviction(self, tmp_path):
        """When max_entries is exceeded, oldest entries should be evicted."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"), max_entries=3)
        cm.put("https://example.com/1", "one")
        cm.put("https://example.com/2", "two")
        cm.put("https://example.com/3", "three")
        # This should trigger eviction of oldest
        cm.put("https://example.com/4", "four")
        assert cm.get_entry_count() <= 3

    def test_stats_tracking(self, tmp_path):
        """Stats should accurately track all cache operations."""
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        cm.put("https://example.com/x", "data")
        cm.get("https://example.com/x")  # hit
        cm.get("https://example.com/y")  # miss

        assert cm.stats.writes == 1
        assert cm.stats.hits == 1
        assert cm.stats.misses == 1
        assert cm.stats.total_lookups == 2
        assert cm.stats.hit_rate == 50.0

    def test_empty_cache_dir(self, tmp_path):
        """Operations on nonexistent cache dir should not raise."""
        cm = CacheManager(cache_dir=str(tmp_path / "nonexistent"))
        assert cm.get_entry_count() == 0
        assert cm.get_total_size_bytes() == 0
        assert cm.evict_expired() == 0
