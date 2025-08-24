import asyncio
import time
from enum import Enum
from typing import Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time and time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker moved to HALF_OPEN state")
            return self.state == CircuitState.OPEN
        return False
        
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half open"""
        return self.state == CircuitState.HALF_OPEN
        
    def call_succeeded(self):
        """Record a successful call"""
        self.failure_count = 0
        self.last_failure_time = None
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker moved to CLOSED state")
            
    def call_failed(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker moved to OPEN state after {self.failure_count} failures")
            
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call a function with circuit breaker protection"""
        if self.is_open():
            raise CircuitBreakerOpenException("Circuit breaker is open")
            
        try:
            result = await func(*args, **kwargs)
            self.call_succeeded()
            return result
        except Exception as e:
            self.call_failed()
            raise e

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

# Global circuit breakers for services
circuit_breakers: Dict[str, CircuitBreaker] = {}