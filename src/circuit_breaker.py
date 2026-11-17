"""
Scraper Circuit Breaker Pattern.
Detects cascading network failures or downed remote sandbox servers,
tripping open to halt outbound traffic and prevent aggressive retries.
"""

from __future__ import annotations

import time
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal healthy operation
    OPEN = "OPEN"          # Tripped, blocking requests to protect host
    HALF_OPEN = "HALF_OPEN"# Testing recovery with a single probe request


class ScraperCircuitBreaker:
    """
    State-machine Circuit Breaker tailored for respectful web crawlers.

    Args:
        failure_threshold: Consecutive server/network errors required to trip circuit.
        recovery_timeout: Seconds to wait in OPEN state before testing recovery.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state, checking for timeout transition."""
        if self._state == CircuitState.OPEN and self._opened_at:
            if (time.monotonic() - self._opened_at) >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def can_execute(self) -> bool:
        """Check whether outbound requests are currently permitted."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        """Register successful response, resetting error counters."""
        self._consecutive_failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None

    def record_failure(self) -> None:
        """Register server/network failure, tripping open if threshold is reached."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()

    def reset(self) -> None:
        """Manually force circuit breaker to healthy CLOSED state."""
        self._consecutive_failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None
