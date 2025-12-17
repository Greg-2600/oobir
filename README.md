Run everything in Docker (recommended for older macOS)
--------------------------------------------------

If you prefer to run everything inside Docker (app + Ollama), build and start services with:
Run tests inside the app container:

```bash
docker compose exec app /home/app/oobir/run-tests.sh
```

Run the CLI inside the container (CLI talks to Ollama at `http://ollama:11434` inside the compose network):

```bash
docker compose exec app python flow.py --host http://ollama:11434 AAPL get_ai_fundamental_analysis
```
# OOBIR — Stock Analysis & Recommendation Engine

FastAPI-based REST API for fetching stock market data (via `yfinance`) and generating AI-powered analysis using Ollama. Includes both CLI and REST API interfaces with comprehensive health monitoring and error handling.

## Quick Start

### Prerequisites
- Python 3.11+ for local runs
- Docker & Docker Compose (recommended for deployment)
- Ollama service (for AI analysis features)

### Local Setup (CLI)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Local Usage — CLI

**Call a single function:**
```bash
python flow.py AAPL get_fundamentals
```

**Run an AI-assisted function** (requires Ollama):
```bash
# Using remote Ollama at 192.168.1.248:11435
python flow.py --host http://192.168.1.248:11435 AAPL get_ai_fundamental_analysis

# Or set OLLAMA_HOST environment variable
OLLAMA_HOST=http://192.168.1.248:11435 python flow.py AAPL get_ai_fundamental_analysis
```

**List available functions:**
```bash
python flow.py --list
```

### Available Functions

**Data Functions:**
- `get_fundamentals` – quarterly fundamentals
- `get_price_history` – historical price data
- `get_analyst_price_targets` – analyst targets
- `get_calendar` – earnings/events calendar
- `get_quarterly_income_stmt` – quarterly income statement
- `get_balance_sheet` – balance sheet data
- `get_option_chain` – option chain data
- `get_news` – recent news items
- `get_screen_undervalued_large_caps` – stock screener

**AI Analysis Functions** (requires Ollama):
- `get_ai_fundamental_analysis` – AI analysis of fundamentals
- `get_ai_balance_sheet_analysis` – AI analysis of balance sheet
- `get_ai_quarterly_income_stm_analysis` – AI analysis of income statement
- `get_ai_technical_analysis` – AI technical analysis
- `get_ai_action_recommendation` – AI buy/sell/hold recommendation
- `get_ai_action_recommendation_sentence` – recommendation with reasoning
- `get_ai_action_recommendation_single_word` – one-word recommendation
- `get_ai_full_report` – comprehensive AI report

## Docker Deployment (Recommended)

### Quick Deploy with Docker Compose

```bash
# Start all services (app + ollama)
docker compose up -d

# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/health/ollama

# View API documentation
open http://localhost:8000/docs
```

### Remote Deployment

Use the automated deployment script:

```bash
./deploy_remote.sh greg@192.168.1.248 ~/oobir
```

Or see [DOCKER.md](DOCKER.md) for manual deployment instructions including:
- Setting up Ollama service on a Linux server
- Building and deploying the app container
- Running tests inside the container
- Accessing the REST API from your local machine

## REST API

The FastAPI application (`flow_api.py`) exposes all stock data and AI analysis functions as REST endpoints with comprehensive health monitoring, logging, and error handling.

### Running the API

**With Docker Compose (Recommended):**
```bash
docker compose up -d
# API available at http://localhost:8000
# Ollama available internally at http://ollama:11434
```

**Locally (Development):**
```bash
pip install fastapi uvicorn requests
python flow_api.py
# API available at http://localhost:8000
# Requires Ollama running separately
```

### Key Features

- **Health Monitoring**: `/health` and `/health/ollama` endpoints
- **Comprehensive Logging**: INFO-level logging with timestamps
- **Proper Error Handling**: Returns 503 when AI services unavailable
- **Auto-generated Docs**: Interactive API docs at `/docs`
- **23 Endpoints**: Data retrieval, AI analysis, and system monitoring

### API Endpoints

**Interactive API docs** (auto-generated):
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`

**Health check endpoints:**
- `GET /health` – Basic service health check
- `GET /health/ollama` – Ollama connectivity test (returns 503 if unreachable)

**Data endpoints:**
- `GET /api/fundamentals/{symbol}` – Fundamentals for a stock
- `GET /api/price-history/{symbol}` – Historical prices
- `GET /api/analyst-targets/{symbol}` – Analyst price targets
- `GET /api/calendar/{symbol}` – Events calendar
- `GET /api/income-stmt/{symbol}` – Quarterly income statement
- `GET /api/balance-sheet/{symbol}` – Balance sheet
- `GET /api/option-chain/{symbol}` – Option chain data
- `GET /api/news/{symbol}` – Recent news
- `GET /api/screen-undervalued` – Stock screener results

**AI analysis endpoints:**
- `GET /api/ai/fundamental-analysis/{symbol}` – AI fundamentals analysis
- `GET /api/ai/balance-sheet-analysis/{symbol}` – AI balance sheet analysis
- `GET /api/ai/income-stmt-analysis/{symbol}` – AI income statement analysis
- `GET /api/ai/technical-analysis/{symbol}` – AI technical analysis
- `GET /api/ai/action-recommendation/{symbol}` – AI recommendation (full)
- `GET /api/ai/action-recommendation-sentence/{symbol}` – AI recommendation (with reasoning)
- `GET /api/ai/action-recommendation-word/{symbol}` – AI recommendation (one word)
- `GET /api/ai/full-report/{symbol}` – Comprehensive AI report

### Example API Calls

```bash
# Check API health
curl http://localhost:8000/health

# Check Ollama connectivity
curl http://localhost:8000/health/ollama

# Get fundamentals for AAPL
curl http://localhost:8000/api/fundamentals/AAPL

# Get AI recommendation for CHTR
curl http://localhost:8000/api/ai/action-recommendation/CHTR

# View API documentation
open http://localhost:8000/docs
```

## Testing

### Run Unit Tests

```bash
# In virtual environment
python -m pytest -v

# Or with unittest
python -m unittest discover -v
```

### Run API Tests

```bash
# Test all 23 endpoints against running API
python test_apis.py http://localhost:8000

# Or test specific API endpoints with pytest
python -m pytest tests/test_flow_api.py -v
```

### Test Inside Docker Container

```bash
# Run all tests
docker compose exec app python -m pytest -v

# Test API endpoints from inside container
docker compose exec app curl http://localhost:8000/health
docker compose exec app curl http://localhost:8000/api/fundamentals/AAPL
```

### Health Checks

```bash
# Check API service
curl http://localhost:8000/health

# Check Ollama connectivity
curl http://localhost:8000/health/ollama

# Remote deployment
curl http://192.168.1.248:8000/health/ollama
```

## Key Features

- **Real-time Stock Data**: Fundamentals, price history, analyst targets, news, options, and more via yfinance
- **AI-Powered Analysis**: Leverages Ollama LLMs for fundamental analysis, technical analysis, and investment recommendations
- **REST API**: 23 endpoints with auto-generated OpenAPI documentation (Swagger UI at `/docs`)
- **Health Monitoring**: Built-in health checks for API and Ollama connectivity
- **Comprehensive Logging**: INFO-level logging with timestamps for debugging and monitoring
- **Proper Error Handling**: Returns appropriate HTTP status codes (503 when AI unavailable)
- **Docker-Ready**: Complete Docker Compose setup with app and Ollama services
- **Well-Tested**: Unit tests, integration tests, and API endpoint tests
- **CLI & API**: Use via command line or REST API

## Architecture

- **FastAPI Application** (`flow_api.py`): REST API with 23 endpoints
- **Core Logic** (`flow.py`): Stock data fetching and AI analysis functions
- **Ollama Integration**: LLM-powered analysis via `huihui_ai/llama3.2-abliterate:3b` model
- **Docker Compose**: Two services (app + ollama) with shared network
- **Health Monitoring**: `/health` and `/health/ollama` endpoints
- **Logging**: Structured logging with timestamps for debugging

## Deployment Options

### Option 1: Automated Remote Deployment

```bash
./deploy_remote.sh greg@192.168.1.248 ~/oobir
```

This script:
- Syncs code to remote host via rsync/tar
- Installs Docker if needed
- Starts containers via docker-compose
- Pulls required Ollama model
- Runs tests to verify deployment

### Option 2: Local Docker Compose

```bash
docker compose up -d
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b
curl http://localhost:8000/health/ollama
```

### Option 3: Local Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python flow_api.py
```

Requires Ollama running separately.

## Ollama Model Setup

This project uses the `huihui_ai/llama3.2-abliterate:3b` model. Install it after starting Ollama:

```bash
# Pull the model
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# Verify installation
docker compose exec ollama ollama list
```

## Troubleshooting

### AI Endpoints Return 503
- **Cause**: Ollama service unreachable or not responding
- **Check**: `curl http://localhost:8000/health/ollama`
- **Fix**: Ensure Ollama container is running and model is loaded
- **Logs**: `docker compose logs ollama` and `docker compose logs app`

### Ollama Connection Issues
```bash
# Check Ollama is running
docker compose ps

# Check Ollama logs
docker compose logs ollama

# Restart Ollama
docker compose restart ollama

# Test Ollama directly
curl http://localhost:11435/api/tags
```

### API Connection Refused
- Verify API server is running: `docker compose ps`
- Check logs: `docker compose logs app`
- Restart services: `docker compose restart app`

### Data Endpoint Errors
- yfinance requires valid ticker symbols (e.g., AAPL, MSFT, TSLA)
- Some data may not be available for all symbols
- Check API logs for specific error messages

### General Tips
- Use `jq` for readable JSON: `curl http://localhost:8000/api/fundamentals/AAPL | jq`
- Check all logs: `docker compose logs`
- View API docs: `http://localhost:8000/docs`
- Test endpoints individually using Swagger UI

## Additional Documentation

- [API_DEPLOYMENT_SUMMARY.md](API_DEPLOYMENT_SUMMARY.md) - Complete deployment guide
- [DOCKER.md](DOCKER.md) - Docker-specific instructions
- [DOCS.md](DOCS.md) - Developer documentation
- [TEST_RESULTS_SUMMARY.md](TEST_RESULTS_SUMMARY.md) - Test results and coverage

## Security Note

⚠️ This API does not include authentication. Use network/firewall restrictions in production environments.

