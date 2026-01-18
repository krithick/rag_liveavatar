# Resilience Testing Guide

## Features Implemented

### 1. Retry Logic with Exponential Backoff
- **Max Attempts**: Configurable (default: 3)
- **Base Delay**: 1 second (configurable)
- **Max Delay**: 10 seconds (configurable)
- **Exponential**: Delay doubles each retry (1s → 2s → 4s)

### 2. Circuit Breaker Pattern
Two independent circuit breakers:

**Azure Circuit Breaker**
- Protects Azure OpenAI Realtime API connections
- Failure threshold: 5 (configurable)
- Timeout: 60 seconds
- States: CLOSED → OPEN → HALF_OPEN → CLOSED

**RAG Circuit Breaker**
- Protects RAG search operations
- Failure threshold: 3 (configurable)
- Timeout: 30 seconds

### 3. Auto-Reconnection
- Detects Azure WebSocket disconnections
- Automatically attempts reconnection
- Tracks reconnection metrics

### 4. Connection Health
- Ping/pong keepalive (20s interval)
- Send timeout protection (5s)
- Connection state validation

## Configuration

Edit `.env` file:

```bash
# Retry Configuration
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=10.0

# Circuit Breaker - Azure
AZURE_CIRCUIT_FAILURE_THRESHOLD=5
AZURE_CIRCUIT_TIMEOUT=60

# Circuit Breaker - RAG
RAG_CIRCUIT_FAILURE_THRESHOLD=3
RAG_CIRCUIT_TIMEOUT=30
```

## Testing

### Unit Tests
```bash
# Test retry logic and circuit breakers
pytest test_resilience.py -v

# Test all
pytest -v
```

### Load Testing
```bash
# Test with 10 concurrent connections for 30s
python test_load.py <kb_id> load

# Stress test reconnections
python test_load.py <kb_id> stress
```

### Manual Testing

**Test Circuit Breaker:**
1. Stop Azure service temporarily
2. Make 5+ requests (Azure circuit opens)
3. Check health endpoint: `curl http://localhost:8003/health`
4. Should show `"azure": "open"`
5. Restart Azure service
6. Wait 60s (timeout period)
7. Circuit transitions to HALF_OPEN, then CLOSED

**Test Auto-Reconnection:**
1. Start server and connect client
2. Simulate network interruption
3. Check logs for `[WS] Attempting to reconnect to Azure...`
4. Connection should restore automatically

**Test Retry Logic:**
1. Introduce temporary network latency
2. Watch logs for `[RETRY] Attempt X failed, retrying in Ys`
3. Should succeed after retries

## Monitoring

### Health Check
```bash
curl http://localhost:8003/health
```

Response includes circuit breaker states:
```json
{
  "status": "healthy",
  "circuit_breakers": {
    "azure": "closed",
    "rag": "closed"
  },
  "metrics": {
    "counters": {
      "azure_connections": 10,
      "azure_reconnections": 2,
      "rag_searches": 50
    },
    "errors": {
      "azure_timeout": 1,
      "rag_search_failed": 0
    },
    "avg_latencies": {
      "azure_connect": 0.234,
      "rag_search": 0.156
    }
  }
}
```

### Key Metrics

**Counters:**
- `azure_connections` - Total Azure connections
- `azure_reconnections` - Successful reconnections
- `rag_searches` - Total RAG searches
- `ws_connections` - WebSocket connections
- `ws_disconnects` - Client disconnects

**Errors:**
- `azure_timeout` - Azure connection timeouts
- `azure_connection_failed` - Azure connection failures
- `azure_disconnected` - Azure disconnections
- `rag_search_failed` - RAG search failures
- `client_timeout` - Client initialization timeouts

**Latencies:**
- `azure_connect` - Average Azure connection time
- `rag_search` - Average RAG search time
- `rag_init` - RAG service initialization time

## Failure Scenarios

### Scenario 1: Azure API Temporary Outage
**Behavior:**
1. First request fails
2. Retry with 1s delay
3. Retry with 2s delay
4. If all fail, circuit opens
5. Subsequent requests rejected for 60s
6. After timeout, circuit tries HALF_OPEN
7. Success → circuit closes

### Scenario 2: Network Interruption
**Behavior:**
1. WebSocket detects disconnection
2. Logs: `[WS] Azure disconnected`
3. Attempts reconnection with retry
4. If successful: `[WS] Reconnected to Azure`
5. Increments `azure_reconnections` metric

### Scenario 3: RAG Search Failure
**Behavior:**
1. Embedding generation fails
2. Retry with exponential backoff
3. If all retries fail, return fallback message
4. Circuit breaker tracks failures
5. Opens after 3 consecutive failures

### Scenario 4: High Load
**Behavior:**
1. Multiple concurrent connections
2. Each has independent retry logic
3. Circuit breaker shared across all
4. If threshold reached, all requests rejected
5. Prevents cascading failures

## Best Practices

1. **Monitor circuit breaker states** - Open circuits indicate systemic issues
2. **Track reconnection rate** - High rate suggests network instability
3. **Watch average latencies** - Increasing latency may predict failures
4. **Set appropriate thresholds** - Balance between resilience and responsiveness
5. **Test failure scenarios** - Regularly validate resilience mechanisms

## Troubleshooting

**Circuit stays OPEN:**
- Check Azure service availability
- Verify credentials and endpoints
- Increase timeout if transient issues

**Frequent reconnections:**
- Check network stability
- Increase ping interval
- Verify firewall/proxy settings

**High retry count:**
- Investigate root cause of failures
- May need to increase timeouts
- Check Azure service quotas
