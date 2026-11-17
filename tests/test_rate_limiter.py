"""
Unit tests for TokenBucketRateLimiter (src/rate_limiter.py).
"""

import time

import pytest

from src.rate_limiter import TokenBucketRateLimiter


def test_rate_limiter_immediate_burst():
    # Capacity 2 tokens, rate 10/sec
    limiter = TokenBucketRateLimiter(requests_per_second=10.0, burst_capacity=2.0)
    # First token immediate
    w1 = limiter.acquire(1.0)
    assert w1 == 0.0
    # Second token immediate from burst
    w2 = limiter.acquire(1.0)
    assert w2 == 0.0


def test_rate_limiter_pacing():
    # Rate of 20/sec = 0.05s per token
    limiter = TokenBucketRateLimiter(requests_per_second=20.0, burst_capacity=1.0)
    limiter.acquire(1.0)  # Consumes full burst
    start = time.monotonic()
    waited = limiter.acquire(1.0)
    elapsed = time.monotonic() - start

    assert waited > 0.03
    assert elapsed >= 0.03


def test_rate_limiter_context_manager():
    limiter = TokenBucketRateLimiter(requests_per_second=50.0, burst_capacity=1.0)
    with limiter.limit() as waited:
        assert waited == 0.0


def test_rate_limiter_invalid_rate():
    with pytest.raises(ValueError):
        TokenBucketRateLimiter(requests_per_second=-1.0)
