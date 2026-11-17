"""
Unit tests for ScraperCircuitBreaker (src/circuit_breaker.py).
"""

import time

from src.circuit_breaker import CircuitState, ScraperCircuitBreaker


def test_circuit_breaker_initial_state():
    cb = ScraperCircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


def test_circuit_breaker_trips_open_on_threshold():
    cb = ScraperCircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    # Tripped
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False


def test_circuit_breaker_recovery_to_half_open_and_closed():
    cb = ScraperCircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.06)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.can_execute() is True

    # Successful probe closes the circuit
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


def test_circuit_breaker_reset():
    cb = ScraperCircuitBreaker(failure_threshold=1)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb.reset()
    assert cb.state == CircuitState.CLOSED
