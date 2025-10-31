import pytest
import time
from unittest.mock import AsyncMock
import asyncio

from app.utils.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenException

class TestCircuitBreaker:
    """Test suite for the Circuit Breaker implementation"""
    
    def test_initial_state(self):
        """Test that circuit breaker starts in closed state"""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
    
    def test_call_succeeded_resets_failure_count(self):
        """Test that successful calls reset failure count"""
        cb = CircuitBreaker()
        cb.failure_count = 2
        cb.last_failure_time = time.time()
        
        cb.call_succeeded()
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
    
    def test_call_failed_increments_count(self):
        """Test that failed calls increment failure count"""
        cb = CircuitBreaker()
        initial_time = time.time()
        
        cb.call_failed()
        assert cb.failure_count == 1
        assert cb.last_failure_time >= initial_time
    
    def test_closed_state_transitions(self):
        """Test state transitions in closed state"""
        # Create circuit breaker with failure threshold of 3
        cb = CircuitBreaker(failure_threshold=3)
        
        # Should remain closed after 1 failure
        cb.call_failed()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1
        
        # Should remain closed after 2 failures
        cb.call_failed()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2
        
        # Should open after 3 failures
        cb.call_failed()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_open_state_blocks_calls(self):
        """Test that open state blocks calls"""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        # Should raise exception when trying to call in open state
        with pytest.raises(CircuitBreakerOpenException):
            await cb.call(asyncio.sleep, 0)  # Use a simple async function
    
    def test_half_open_transitions(self):
        """Test transitions to and from half-open state"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)
        
        # Force circuit breaker to open state
        cb.call_failed()
        cb.call_failed()
        assert cb.state == CircuitState.OPEN
        
        # Simulate timeout by setting last failure time in the past
        cb.last_failure_time = time.time() - 2
        
        # Check if it transitions to half-open
        assert cb.is_open() == False  # Should transition to half-open
        assert cb.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self):
        """Test that success in half-open state closes circuit"""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN
        
        # Successful call should close circuit
        async def success_func():
            return "success"
            
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self):
        """Test that failure in half-open state reopens circuit"""
        cb = CircuitBreaker(failure_threshold=1)  # Set threshold to 1 for immediate opening
        cb.state = CircuitState.HALF_OPEN
        
        # Failed call should reopen circuit
        async def fail_func():
            raise Exception("Test failure")
        
        with pytest.raises(Exception):
            await cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 1
    
    def test_is_open_timeout_logic(self):
        """Test the timeout logic in is_open method"""
        cb = CircuitBreaker(timeout=1)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 2  # 2 seconds ago
        
        # Should return False and transition to half-open
        assert cb.is_open() == False
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_is_open_no_timeout(self):
        """Test is_open when timeout hasn't expired"""
        cb = CircuitBreaker(timeout=5)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 2  # 2 seconds ago
        
        # Should return True (still open)
        assert cb.is_open() == True
        assert cb.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_call_with_function(self):
        """Test calling a function through the circuit breaker"""
        cb = CircuitBreaker()
        
        # Successful call
        async def success_func():
            return "test result"
            
        result = await cb.call(success_func)
        assert result == "test result"
        
        # Failed call
        async def fail_func():
            raise ValueError("Test error")
            
        with pytest.raises(ValueError):
            await cb.call(fail_func)
    
    def test_call_with_async_function(self):
        """Test calling an async function through the circuit breaker"""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_call_with_async_awaitable(self):
        """Test calling with an awaitable"""
        cb = CircuitBreaker()
        
        async def sample_function():
            return "success"
        
        # Mock the async function
        mock_func = AsyncMock(return_value="mocked result")
        
        # Test with mocked async function
        result = await cb.call(mock_func)
        assert result == "mocked result"
        mock_func.assert_called_once()
    
    def test_custom_threshold_and_timeout(self):
        """Test circuit breaker with custom threshold and timeout"""
        cb = CircuitBreaker(failure_threshold=5, timeout=10)
        
        assert cb.failure_threshold == 5
        assert cb.timeout == 10
        
        # Test that it takes 5 failures to open
        for i in range(4):
            cb.call_failed()
            assert cb.state == CircuitState.CLOSED
        
        cb.call_failed()
        assert cb.state == CircuitState.OPEN
    
    def test_manual_reset_functionality(self):
        """Test manual reset functionality by directly setting attributes"""
        cb = CircuitBreaker()
        
        # Force to open state
        cb.state = CircuitState.OPEN
        cb.failure_count = 3
        cb.last_failure_time = time.time()
        
        # Manual reset by setting attributes
        cb.state = CircuitState.CLOSED
        cb.failure_count = 0
        cb.last_failure_time = None
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None