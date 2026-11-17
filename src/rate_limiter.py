"""
Thread-safe Token Bucket Rate Limiter.
Ensures scraper strictly adheres to polite inter-request intervals,
preventing server overload even under multi-threaded concurrency.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Generator


class TokenBucketRateLimiter:
    """
    Token Bucket rate limiter for respectful crawling.

    Args:
        requests_per_second: Maximum steady-state request rate (e.g., 2.0 = 500ms delay).
        burst_capacity: Maximum number of tokens that can accumulate during idle periods.
    """

    def __init__(self, requests_per_second: float = 2.0, burst_capacity: float = 2.0):
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        self.rate = requests_per_second
        self.burst_capacity = max(1.0, burst_capacity)
        self.tokens = self.burst_capacity
        self.last_update = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens_needed: float = 1.0) -> float:
        """
        Block until sufficient tokens are available.
        Returns the duration waited in seconds.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now

            # Replenish tokens based on elapsed time
            self.tokens = min(self.burst_capacity, self.tokens + elapsed * self.rate)

            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return 0.0

            # Compute required wait time
            deficit = tokens_needed - self.tokens
            wait_time = deficit / self.rate
            self.tokens = 0.0
            self.last_update = now + wait_time

        time.sleep(wait_time)
        return wait_time

    @contextmanager
    def limit(self, tokens_needed: float = 1.0) -> Generator[float, None, None]:
        """Context manager syntax for rate limited blocks."""
        waited = self.acquire(tokens_needed)
        try:
            yield waited
        finally:
            pass

    def get_available_tokens(self) -> float:
        """Inspect current token count without consuming."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            return min(self.burst_capacity, self.tokens + elapsed * self.rate)
