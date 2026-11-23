"""
Retry policy and resilient HTTP fetching module.
Implements polite retry logic for transient errors (timeouts, 5xx),
token-bucket rate limiting pacing, and circuit breaker protection
while strictly forbidding retries on definitive client errors (404, 403).
"""

from __future__ import annotations

import time

import requests

from src.circuit_breaker import ScraperCircuitBreaker
from src.rate_limiter import TokenBucketRateLimiter

DEFAULT_TIMEOUT = 10
RETRY_DELAY = 2.0

# Global shared polite rate limiter and circuit breaker instances
GLOBAL_RATE_LIMITER = TokenBucketRateLimiter(requests_per_second=2.0, burst_capacity=2.0)
GLOBAL_CIRCUIT_BREAKER = ScraperCircuitBreaker(failure_threshold=5, recovery_timeout=30.0)


def should_retry(status_code: int | None, exc: Exception | None) -> bool:
    """
    Determine whether a failed request should be retried.
    - 404 (Not Found): DO NOT RETRY (page does not exist).
    - 403 (Forbidden): DO NOT RETRY (server denied access; do not become a pest).
    - 5xx (Server Error) or Timeout/ConnectionError: RETRY ONCE after a brief pause.
    """
    if status_code in (404, 403):
        return False
    if status_code and 500 <= status_code < 600:
        return True
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    return False


def polite_get_with_retry(
    url: str,
    user_agent: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 1,
    rate_limiter: TokenBucketRateLimiter | None = None,
    circuit_breaker: ScraperCircuitBreaker | None = None,
) -> tuple[requests.Response | None, int | None, Exception | None]:
    """
    Send an HTTP GET request with polite rate limiting, circuit breaker protection,
    and single-retry on transient errors.

    Returns:
        tuple (response, status_code, exception)
    """
    limiter = rate_limiter or GLOBAL_RATE_LIMITER
    cb = circuit_breaker or GLOBAL_CIRCUIT_BREAKER

    # Check circuit breaker before hitting the wire
    if not cb.can_execute():
        return None, 503, requests.ConnectionError("Circuit breaker tripped OPEN — request blocked.")

    req_headers = dict(headers or {})
    if user_agent and "User-Agent" not in req_headers:
        req_headers["User-Agent"] = user_agent

    attempt = 0

    while attempt <= max_retries:
        attempt += 1

        # Enforce rate limiter pacing
        limiter.acquire(1.0)

        try:
            resp = requests.get(url, headers=req_headers, timeout=timeout)
            if resp.status_code == 200:
                cb.record_success()
                return resp, 200, None

            # Check if this status warrants a retry
            if should_retry(resp.status_code, None) and attempt <= max_retries:
                cb.record_failure()
                time.sleep(RETRY_DELAY)
                continue

            if resp.status_code >= 500:
                cb.record_failure()
            elif resp.status_code == 200:
                cb.record_success()

            return resp, resp.status_code, None

        except requests.RequestException as exc:
            cb.record_failure()
            if should_retry(None, exc) and attempt <= max_retries:
                time.sleep(RETRY_DELAY)
                continue
            return None, None, exc

    return None, None, None
