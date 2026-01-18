"""
Resilience testing: retry, circuit breaker
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from resilience import retry_async, retry_sync, CircuitBreaker, CircuitState

@pytest.mark.asyncio
async def test_retry_async_success_first_attempt():
    """Test successful async retry on first attempt"""
    mock_func = AsyncMock(return_value="success")
    result = await retry_async(mock_func, max_attempts=3)
    assert result == "success"
    assert mock_func.call_count == 1

@pytest.mark.asyncio
async def test_retry_async_success_after_failures():
    """Test async retry succeeds after failures"""
    mock_func = AsyncMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
    result = await retry_async(mock_func, max_attempts=3, base_delay=0.1)
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_retry_async_all_attempts_fail():
    """Test async retry fails after all attempts"""
    mock_func = AsyncMock(side_effect=Exception("fail"))
    with pytest.raises(Exception):
        await retry_async(mock_func, max_attempts=3, base_delay=0.1)
    assert mock_func.call_count == 3

def test_retry_sync_success():
    """Test successful sync retry"""
    mock_func = Mock(return_value="success")
    result = retry_sync(mock_func, max_attempts=3)
    assert result == "success"
    assert mock_func.call_count == 1

def test_retry_sync_exponential_backoff():
    """Test exponential backoff in sync retry"""
    mock_func = Mock(side_effect=[Exception("fail"), "success"])
    result = retry_sync(mock_func, max_attempts=3, base_delay=0.1, exponential=True)
    assert result == "success"
    assert mock_func.call_count == 2

def test_circuit_breaker_closed_state():
    """Test circuit breaker in closed state"""
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state == CircuitState.CLOSED
    
    result = cb.call(lambda: "success")
    assert result == "success"
    assert cb.state == CircuitState.CLOSED

def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold"""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)
    
    for _ in range(3):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except:
            pass
    
    assert cb.state == CircuitState.OPEN
    
    # Should reject calls when open
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        cb.call(lambda: "success")

@pytest.mark.asyncio
async def test_circuit_breaker_async_opens():
    """Test async circuit breaker opens after failures"""
    cb = CircuitBreaker(failure_threshold=2, timeout=1)
    
    async def failing_func():
        raise Exception("fail")
    
    for _ in range(2):
        try:
            await cb.call_async(failing_func)
        except:
            pass
    
    assert cb.state == CircuitState.OPEN

def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker recovers through half-open state"""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1, half_open_attempts=2)
    
    # Trigger failures to open circuit
    for _ in range(2):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except:
            pass
    
    assert cb.state == CircuitState.OPEN
    
    # Wait for timeout
    import time
    time.sleep(0.2)
    
    # Should transition to half-open and allow attempts
    cb.call(lambda: "success")
    assert cb.state == CircuitState.HALF_OPEN
    
    # Second success should close circuit
    cb.call(lambda: "success")
    assert cb.state == CircuitState.CLOSED

def test_circuit_breaker_half_open_failure():
    """Test circuit breaker returns to open on half-open failure"""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
    
    # Open circuit
    for _ in range(2):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except:
            pass
    
    import time
    time.sleep(0.2)
    
    # Fail in half-open state
    try:
        cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
    except:
        pass
    
    assert cb.state == CircuitState.OPEN
