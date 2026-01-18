"""
Monitoring and metrics
"""
import time
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Metrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = {}
        self.errors = defaultdict(int)
        self.start_time = time.time()
        self.latencies = defaultdict(list)  # Track latency history
    
    def increment(self, metric: str, value: int = 1):
        self.counters[metric] += value
    
    def start_timer(self, operation: str):
        self.timers[operation] = time.time()
    
    def end_timer(self, operation: str):
        if operation in self.timers:
            duration = time.time() - self.timers[operation]
            logger.info(f"[METRIC] {operation}: {duration:.3f}s")
            self.latencies[operation].append(duration)
            # Keep only last 100 measurements
            if len(self.latencies[operation]) > 100:
                self.latencies[operation].pop(0)
            del self.timers[operation]
            return duration
        return None
    
    def record_error(self, error_type: str):
        self.errors[error_type] += 1
        self.increment("total_errors")
    
    def get_stats(self):
        uptime = time.time() - self.start_time
        
        # Calculate average latencies
        avg_latencies = {}
        for op, times in self.latencies.items():
            if times:
                avg_latencies[op] = round(sum(times) / len(times), 3)
        
        return {
            "uptime_seconds": round(uptime, 2),
            "counters": dict(self.counters),
            "errors": dict(self.errors),
            "avg_latencies": avg_latencies,
            "timestamp": datetime.utcnow().isoformat()
        }

metrics = Metrics()
