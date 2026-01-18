# Deployment Guide

## Region-Based Configuration

### 1. Choose Your Environment

Copy the appropriate environment file:

```bash
# Development (East US)
cp .env.dev .env

# Staging (Southeast Asia)
cp .env.staging .env

# Production (West Europe)
cp .env.prod .env
```

### 2. Update Credentials

Edit `.env` with your actual Azure credentials for the selected region.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_rag_service.py -v
```

### 5. Start Server

```bash
python app.py
```

## Health Check

Once running, check health:

```bash
curl http://localhost:8003/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "dev",
  "rag_service": "healthy",
  "metrics": {
    "uptime_seconds": 123.45,
    "counters": {},
    "errors": {}
  }
}
```

## Monitoring

View metrics:
```bash
curl http://localhost:8003/metrics
```

## Available Regions

- **East US**: Low latency for North America
- **West Europe**: Low latency for Europe/Africa
- **Southeast Asia**: Low latency for Asia-Pacific

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `dev`, `staging`, `prod` |
| `AZURE_RESOURCE` | Azure OpenAI resource name | `myresource-eastus` |
| `AZURE_CONNECTION_TIMEOUT` | Connection timeout (seconds) | `10` |
| `CLIENT_INIT_TIMEOUT` | Client init timeout (seconds) | `30` |

## Troubleshooting

1. **Health check fails**: Check Azure credentials
2. **Connection timeout**: Increase `AZURE_CONNECTION_TIMEOUT`
3. **RAG search fails**: Verify Azure Search endpoint and index name
