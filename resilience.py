"""
Resilience patterns: retry, circuit breaker
"""
import asyncio
import time
from functools import wraps
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60, half_open_attempts=3):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.success_count = 0
    
    def call(self, func):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("[CIRCUIT] Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    async def call_async(self, func):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("[CIRCUIT] Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_attempts:
                logger.info("[CIRCUIT] Recovered, transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("[CIRCUIT] Failed in HALF_OPEN, back to OPEN")
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.error(f"[CIRCUIT] Threshold reached ({self.failure_count}), opening circuit")
            self.state = CircuitState.OPEN

async def retry_async(func, max_attempts=3, base_delay=1.0, max_delay=10.0, exponential=True):
    """Retry async function with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                logger.error(f"[RETRY] Failed after {max_attempts} attempts: {e}")
                raise
            
            delay = base_delay * (2 ** attempt) if exponential else base_delay
            delay = min(delay, max_delay)
            logger.warning(f"[RETRY] Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)

def retry_sync(func, max_attempts=3, base_delay=1.0, max_delay=10.0, exponential=True):
    """Retry sync function with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                logger.error(f"[RETRY] Failed after {max_attempts} attempts: {e}")
                raise
            
            delay = base_delay * (2 ** attempt) if exponential else base_delay
            delay = min(delay, max_delay)
            logger.warning(f"[RETRY] Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            time.sleep(delay)

# Global circuit breakers
azure_circuit = CircuitBreaker(
    failure_threshold=5,  # Will be overridden by config
    timeout=60
)
rag_circuit = CircuitBreaker(
    failure_threshold=3,
    timeout=30
)

def init_circuit_breakers(config):
    """Initialize circuit breakers with config values"""
    global azure_circuit, rag_circuit
    azure_circuit.failure_threshold = config.AZURE_CIRCUIT_FAILURE_THRESHOLD
    azure_circuit.timeout = config.AZURE_CIRCUIT_TIMEOUT
    rag_circuit.failure_threshold = config.RAG_CIRCUIT_FAILURE_THRESHOLD
    rag_circuit.timeout = config.RAG_CIRCUIT_TIMEOUT
