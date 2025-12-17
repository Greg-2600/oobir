# Docker & Ollama Setup Guide for OOBIR

Complete instructions for running OOBIR with Docker Compose, including both local Ollama setup and full containerized deployment.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Local Ollama Setup](#local-ollama-setup)
3. [Full Containerized Deployment](#full-containerized-deployment)
4. [REST API via Docker](#rest-api-via-docker)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Port 8000 available (API) and 11434/11435 (Ollama)

### Start All Services (Recommended)

```bash
# Build and start all services
docker compose up -d --build

# Pull the required AI model
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# Verify services are healthy
curl http://localhost:8000/health
curl http://localhost:8000/health/ollama

# Access the API
open http://localhost:8000/docs  # Interactive documentation
```

---

## Local Ollama Setup

### Running a Local Ollama Container (for `flow.py`)

This section shows how to run a standalone Ollama service and point `flow.py` at it for AI analysis.

### Start the Ollama Container Only

```bash
docker compose up -d ollama
```

### Watch Logs (Optional)

```bash
docker compose logs -f ollama
```

When the container is healthy and listening on host port `11435` (internal port 11434), you can use `flow.py`:

```bash
# Activate virtual environment
source venv/bin/activate

# Run flow.py with local Ollama
python flow.py --host http://localhost:11435 AAPL get_ai_fundamental_analysis
```

### Install the Required Model

Ollama requires models to be installed before AI calls work. After the container is running:

```bash
# Pull the required model
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# Verify installed models
docker compose exec ollama ollama list
```

### Notes on Local Ollama Setup
- The Compose file uses `ollama/ollama:latest`; update `docker-compose.yml` if you need a different tag
- Models and state are persisted in the `ollama_data` volume (survives container restarts)
- Ollama is CPU-only by default; enable GPU acceleration if available
- If you previously hit the `librtmp` error when running `flow.py`, that only affected `yfinance`'s transport native libs

---

## Full Containerized Deployment

### Running Everything Inside Docker

This repository includes both `app` and `ollama` services that run on the same Docker network. The app container can call Ollama at `http://ollama:11434` internally.

### Build and Start All Services

```bash
docker compose up -d --build
```

### Pull the AI Model

```bash
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b
```

### Access the Application

```bash
# View API documentation
open http://localhost:8000/docs         # Swagger UI
open http://localhost:8000/redoc        # ReDoc

# Or use curl
curl http://localhost:8000/health
```

### Run Commands Inside the Container

```bash
# Run tests
docker compose exec app python -m pytest -v

# Run the CLI
docker compose exec app python flow.py --host http://ollama:11434 AAPL get_ai_fundamental_analysis

# Open a shell in the container
docker compose exec app bash

# Run the custom test script
docker compose exec app /home/app/oobir/run-tests.sh
```

---

## REST API via Docker

### API Endpoints Overview

The `app` container exposes a FastAPI REST API on port 8000 with **23 endpoints** total:

**Metadata Endpoints (4):**
- `GET /` — API info and current Ollama host
- `GET /docs` — Interactive Swagger UI documentation
- `GET /redoc` — ReDoc alternative documentation
- `GET /openapi.json` — OpenAPI schema

**Health Check Endpoints (2):**
- `GET /health` — Basic service health check
- `GET /health/ollama` — Ollama connectivity test (returns 503 if unreachable)

**Data Endpoints (9):**
- `GET /api/fundamentals/{symbol}` — Company fundamentals
- `GET /api/price-history/{symbol}` — 121-day price history
- `GET /api/analyst-targets/{symbol}` — Analyst price targets
- `GET /api/calendar/{symbol}` — Earnings calendar
- `GET /api/income-stmt/{symbol}` — Quarterly income statement
- `GET /api/balance-sheet/{symbol}` — Balance sheet data
- `GET /api/option-chain/{symbol}` — Option chain data
- `GET /api/news/{symbol}` — Recent news articles
- `GET /api/screen-undervalued` — Stock screener (undervalued stocks)

**AI Analysis Endpoints (8):**
- `GET /api/ai/fundamental-analysis/{symbol}` — AI analysis of fundamentals
- `GET /api/ai/balance-sheet-analysis/{symbol}` — AI analysis of balance sheet
- `GET /api/ai/income-stmt-analysis/{symbol}` — AI analysis of income statement
- `GET /api/ai/technical-analysis/{symbol}` — AI technical analysis
- `GET /api/ai/action-recommendation/{symbol}` — AI recommendation (JSON)
- `GET /api/ai/action-recommendation-sentence/{symbol}` — AI recommendation (sentence)
- `GET /api/ai/action-recommendation-word/{symbol}` — AI recommendation (one word)
- `GET /api/ai/full-report/{symbol}` — Complete AI report

### Example API Calls

```bash
# Check API and Ollama health
curl http://localhost:8000/health
curl http://localhost:8000/health/ollama

# Get fundamentals for AAPL
curl http://localhost:8000/api/fundamentals/AAPL

# Get AI action recommendation for AAPL
curl http://localhost:8000/api/ai/action-recommendation/AAPL

# Check API metadata
curl http://localhost:8000/
```

### Pretty-Print JSON Responses

Use `jq` for better readability:

```bash
curl -s http://localhost:8000/api/fundamentals/AAPL | jq
```

---

## Testing

### Run Tests Inside the Container

```bash
# Run all tests with pytest
docker compose exec app python -m pytest -v

# Run specific test file
docker compose exec app python -m pytest tests/test_flow.py -v

# Run with unittest discovery
docker compose exec app python -m unittest discover -v
```

### Test All 23 API Endpoints

```bash
# Test data endpoints (9 endpoints)
./test_data_endpoints.sh http://localhost:8000
./test_data_endpoints.sh http://localhost:8000 MSFT

# Test AI endpoints (5 endpoints)
./test_ai_endpoints.sh http://localhost:8000
./test_ai_endpoints.sh http://localhost:8000 AAPL

# Or test against remote container
./test_data_endpoints.sh http://192.168.1.248:8000 CHTR
./test_ai_endpoints.sh http://192.168.1.248:8000 TSLA
```

### Verify Specific Endpoints

```bash
# Test health endpoints
docker compose exec app curl http://localhost:8000/health
docker compose exec app curl http://localhost:8000/health/ollama

# Test data endpoints
docker compose exec app curl http://localhost:8000/api/fundamentals/AAPL
docker compose exec app curl http://localhost:8000/api/price-history/MSFT

# Test AI endpoints
docker compose exec app curl http://localhost:8000/api/ai/action-recommendation-word/TSLA
```

---

## Troubleshooting

### Container Status and Logs

```bash
# Check if all containers are running
docker compose ps

# View logs for all services
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View logs for specific service
docker compose logs app
docker compose logs ollama
```

### API Server Not Responding

```bash
# Verify app container is running
docker compose ps app

# Check app logs for errors
docker compose logs app

# Restart the app container
docker compose restart app

# Rebuild and restart (if code changed)
docker compose up -d --build app
```

### Ollama Not Responding

```bash
# Verify Ollama container is running
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Test Ollama directly
curl http://localhost:11435/api/tags

# Restart Ollama
docker compose restart ollama

# Verify model is installed
docker compose exec ollama ollama list

# Pull model if missing
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b
```

### AI Endpoints Return 503 (Service Unavailable)

**Symptoms:** AI analysis endpoints return HTTP 503 status code

**Causes:**
- Ollama service is not running
- Model is not installed
- Network connectivity issue between app and Ollama

**Diagnostic Steps:**
```bash
# Check Ollama health from API
curl http://localhost:8000/health/ollama

# Test Ollama directly
docker compose exec app curl http://ollama:11434/api/tags

# Check if model is installed
docker compose exec ollama ollama list
```

**Solutions:**
```bash
# Ensure Ollama is running
docker compose start ollama

# Pull the model
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# Restart both services
docker compose restart app ollama
```

### Data Endpoints Return Errors

**Common Issues:**
- Invalid ticker symbol (e.g., typo or delisted stock)
- Data not available for that ticker
- yfinance API rate limiting

**Debugging:**
```bash
# Check app logs for specific errors
docker compose logs app | grep ERROR

# Test a known good ticker
curl http://localhost:8000/api/fundamentals/AAPL

# Use interactive docs to see detailed error messages
open http://localhost:8000/docs
```

### Port Already in Use

```bash
# If port 8000 is in use, find what's using it
lsof -i :8000

# Or use a different port (edit docker-compose.yml)
# Change "8000:8000" to "9000:8000"

# Then access API at http://localhost:9000
```

### Memory or CPU Issues

```bash
# Check container resource usage
docker stats

# If Ollama is running out of memory:
# - Reduce Ollama model size in docker-compose.yml
# - Allocate more memory to Docker Desktop

# Monitor in real-time
docker stats --no-stream
```

---

## Next Steps

- **Quick Start:** Follow [README.md](README.md) for usage examples
- **API Reference:** See [DOCS.md](DOCS.md) for comprehensive API documentation
- **Testing:** Run `./test_data_endpoints.sh` or `./test_ai_endpoints.sh` to verify all endpoints
- **Deployment:** Use [deploy_remote.sh](deploy_remote.sh) for production deployment

---

**Last Updated:** December 17, 2025


