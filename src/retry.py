"""
Retry policy and resilient HTTP fetching module.
Implements polite retry logic for transient errors (timeouts, 5xx)
while strictly forbidding retries on definitive client errors (404, 403).
"""

import time

import requests

DEFAULT_TIMEOUT = 10
RETRY_DELAY = 2.0


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
    user_agent: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 1,
) -> tuple[requests.Response | None, int | None, Exception | None]:
    """
    Send an HTTP GET request with a polite single-retry on transient errors.

    Returns:
        tuple (response, status_code, exception)
    """
    headers = {"User-Agent": user_agent}
    attempt = 0

    while attempt <= max_retries:
        attempt += 1
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp, 200, None

            # Check if this status warrants a retry
            if should_retry(resp.status_code, None) and attempt <= max_retries:
                time.sleep(RETRY_DELAY)
                continue

            return resp, resp.status_code, None

        except requests.RequestException as exc:
            if should_retry(None, exc) and attempt <= max_retries:
                time.sleep(RETRY_DELAY)
                continue
            return None, None, exc

    return None, None, None
