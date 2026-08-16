"""
Production Exponential Backoff & Retry policy.
Features:
- Exponential backoff: 2^attempt * base_delay
- Full jitter (randomness) to prevent thundering herd
- Respects HTTP 429 and standard 'Retry-After' response headers
- Structured logging of retry attempts
"""

import random
import time
from typing import Callable
import requests


def calculate_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> float:
    """
    Calculate exponential backoff with full jitter:
    sleep = random.uniform(0, min(max_delay, base_delay * 2^attempt))
    """
    exponential_cap = min(max_delay, base_delay * (2 ** attempt))
    return random.uniform(0.5, exponential_cap)


def get_retry_after_delay(response: requests.Response | None) -> float | None:
    """
    Parse the Retry-After header if present on a 429 or 503 response.
    Returns delay in seconds, or None.
    """
    if not response or not hasattr(response, "headers"):
        return None

    header_val = response.headers.get("Retry-After")
    if not header_val:
        return None

    try:
        return float(header_val)
    except ValueError:
        return None


def execute_with_exponential_backoff(
    request_fn: Callable[[], requests.Response],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> tuple[requests.Response | None, list[dict]]:
    """
    Execute an HTTP request with exponential backoff and jitter.
    Records structured logs for each attempt.
    """
    attempt_logs = []

    for attempt in range(1, max_attempts + 1):
        try:
            resp = request_fn()
            attempt_logs.append({
                "attempt": attempt,
                "status_code": resp.status_code if resp else None,
                "success": resp.status_code == 200 if resp else False,
            })

            if resp.status_code == 200:
                return resp, attempt_logs

            # Definitive errors: do not retry
            if resp.status_code in (404, 403, 401):
                return resp, attempt_logs

            # Check for Retry-After header
            retry_after = get_retry_after_delay(resp)
            delay = retry_after if retry_after is not None else calculate_backoff_with_jitter(attempt, base_delay, max_delay)

            if attempt < max_attempts:
                time.sleep(delay)

        except requests.RequestException as exc:
            attempt_logs.append({
                "attempt": attempt,
                "exception": str(exc),
                "success": False,
            })
            if attempt < max_attempts:
                delay = calculate_backoff_with_jitter(attempt, base_delay, max_delay)
                time.sleep(delay)

    return None, attempt_logs
