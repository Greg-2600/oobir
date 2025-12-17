# OOBIR — Developer Documentation

Complete reference for using OOBIR's stock analysis and AI recommendation features via CLI or REST API.

## Available Functions

### Data Functions (9)
- `get_fundamentals(ticker)` — Company fundamentals (P/E, market cap, EPS, etc.)
- `get_price_history(ticker)` — 121 days of historical OHLCV data
- `get_analyst_price_targets(ticker)` — Analyst consensus and price targets
- `get_calendar(ticker)` — Earnings dates and corporate events
- `get_quarterly_income_stmt(ticker)` — Quarterly income statement
- `get_balance_sheet(ticker)` — Balance sheet data
- `get_option_chain(ticker)` — Options data (calls/puts)
- `get_news(ticker)` — Recent news articles
- `get_screen_undervalued_large_caps()` — Stock screener for undervalued stocks

### AI Analysis Functions (8)
Requires Ollama with `huihui_ai/llama3.2-abliterate:3b` model:
- `get_ai_fundamental_analysis(ticker)` — AI analysis of fundamentals
- `get_ai_balance_sheet_analysis(ticker)` — AI balance sheet insights
- `get_ai_quarterly_income_stm_analysis(ticker)` — AI income statement analysis
- `get_ai_technical_analysis(ticker)` — AI technical analysis
- `get_ai_action_recommendation(ticker)` — Detailed buy/sell/hold recommendation
- `get_ai_action_recommendation_sentence(ticker)` — One-sentence recommendation
- `get_ai_action_recommendation_single_word(ticker)` — Single word: BUY/SELL/HOLD
- `get_ai_full_report(ticker)` — Comprehensive multi-section AI report

---

## CLI Usage

### Basic Data Retrieval
```bash
# Get fundamentals
python flow.py AAPL get_fundamentals

# Get price history
python flow.py MSFT get_price_history

# Get analyst targets
python flow.py TSLA get_analyst_price_targets
```

### AI Analysis (Requires Ollama)

**Using environment variable:**
```bash
export OLLAMA_HOST=http://192.168.1.248:11435
python flow.py AAPL get_ai_fundamental_analysis
```

**Using --host flag:**
```bash
python flow.py --host http://192.168.1.248:11435 AAPL get_ai_fundamental_analysis
```

**Inside Docker container:**
```bash
docker compose exec app python flow.py --host http://ollama:11434 AAPL get_ai_fundamental_analysis
```

### List Available Functions
```bash
python flow.py --list
```

---

## REST API

---

## REST API

### Starting the API Server

**Production (Docker Compose):**
```bash
docker compose up -d
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Development (Local Python):**
```bash
pip install fastapi uvicorn requests
python -m uvicorn flow_api:app --host 0.0.0.0 --port 8000 --reload
```

**Remote Deployment:**
```bash
./deploy_remote.sh greg@192.168.1.248 ~/oobir
# API: http://192.168.1.248:8000
```

### API Endpoints (23 Total)

**Health & Metadata (6):**
- `GET /` — API info and configuration
- `GET /docs` — Interactive Swagger UI
- `GET /redoc` — Alternative API documentation
- `GET /openapi.json` — OpenAPI schema
- `GET /health` — Basic service health check
- `GET /health/ollama` — Ollama connectivity test (returns 503 if down)

**Data Endpoints (9):**
- `GET /api/fundamentals/{symbol}`
- `GET /api/price-history/{symbol}`
- `GET /api/analyst-targets/{symbol}`
- `GET /api/calendar/{symbol}`
- `GET /api/income-stmt/{symbol}`
- `GET /api/balance-sheet/{symbol}`
- `GET /api/option-chain/{symbol}`
- `GET /api/news/{symbol}`
- `GET /api/screen-undervalued`

**AI Analysis Endpoints (8):**
- `GET /api/ai/fundamental-analysis/{symbol}`
- `GET /api/ai/balance-sheet-analysis/{symbol}`
- `GET /api/ai/income-stmt-analysis/{symbol}`
- `GET /api/ai/technical-analysis/{symbol}`
- `GET /api/ai/action-recommendation/{symbol}`
- `GET /api/ai/action-recommendation-sentence/{symbol}`
- `GET /api/ai/action-recommendation-word/{symbol}`
- `GET /api/ai/full-report/{symbol}`

### API Examples

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/ollama

# Data endpoints
curl http://localhost:8000/api/fundamentals/AAPL
curl http://localhost:8000/api/price-history/MSFT

# AI endpoints
curl http://localhost:8000/api/ai/fundamental-analysis/AAPL
curl http://localhost:8000/api/ai/action-recommendation-word/TSLA

# Pretty print with jq
curl -s http://localhost:8000/api/fundamentals/AAPL | jq
```

### API Features

- **Auto-generated Documentation**: Visit `/docs` for interactive Swagger UI
- **Health Monitoring**: Check API and Ollama status via `/health` endpoints
- **Proper Error Handling**: Returns 503 when AI services unavailable (not 200 with null)
- **Comprehensive Logging**: INFO-level logging with timestamps (`docker compose logs app`)
- **JSON Serialization**: Handles pandas/numpy types, dates, NaN, and Infinity properly

### Environment Variables

- `OLLAMA_HOST`: Ollama service URL
  - Container default: `http://ollama:11434`
  - External default: `http://192.168.1.248:11435`
- `PYTHONUNBUFFERED=1`: Enable real-time logging

---

## Testing

### Unit Tests

```bash
# Run all tests with pytest (recommended)
python -m pytest -v

# Run specific test file
python -m pytest tests/test_flow.py -v

# Run with unittest
python -m unittest discover -v
```

### API Endpoint Tests

```bash
# Test all 23 endpoints against running API
python test_apis.py http://localhost:8000

# Test remote deployment
python test_apis.py http://192.168.1.248:8000

# Run pytest API tests
python -m pytest tests/test_flow_api.py -v
```

### Docker Container Tests

```bash
# Run all tests inside container
docker compose exec app python -m pytest -v

# Run specific test suite
docker compose exec app python -m pytest tests/test_flow.py -v

# Test API from inside container
docker compose exec app curl http://localhost:8000/health
docker compose exec app curl http://localhost:8000/api/fundamentals/AAPL
```

### Test Coverage

- **Unit Tests**: 7 tests covering core flow.py functions
- **Integration Tests**: 16 tests for API endpoints with mocks
- **API Tests**: 23 endpoint tests against live API
- **All tests pass**: ✅

### Setting Up Test Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run tests
python -m pytest -v
```

---

## Development Notes

### Code Architecture

- **flow.py**: Core business logic for data fetching and AI analysis
- **flow_api.py**: FastAPI REST API wrapper (23 endpoints)
- **docker-compose.yml**: Multi-container orchestration (app + ollama)
- **Dockerfile**: Python 3.11-slim container with all dependencies
- **tests/**: Unit and integration test suites

### Key Design Decisions

- **Deferred Ollama Import**: The `ollama` client is imported at runtime so `--host` flag or `OLLAMA_HOST` can override before connection
- **Mock Testing**: Tests mock `yfinance` and `ollama` to avoid network calls
- **Automatic Serialization**: FastAPI endpoints handle pandas/numpy types automatically
- **Graceful Degradation**: AI endpoints return 503 (not 200 with null) when Ollama unavailable
- **Health Monitoring**: `/health/ollama` enables uptime monitoring and alerting

### Error Handling

- **Data Endpoints**: Return 500 with error details if yfinance fails
- **AI Endpoints**: Return 503 if Ollama is unreachable or returns None
- **Validation**: Ticker symbols validated by yfinance
- **Logging**: All errors logged with timestamps for debugging

### Logging Configuration

```python
# INFO-level logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

View logs:
```bash
# Docker logs
docker compose logs app
docker compose logs ollama

# Follow logs in real-time
docker compose logs -f app
```

---

## Troubleshooting

### AI Endpoints Return 503

**Symptoms**: `/api/ai/*` endpoints return 503 status code

**Diagnosis**:
```bash
# Check Ollama health
curl http://localhost:8000/health/ollama

# Check Ollama container
docker compose ps
docker compose logs ollama

# Verify model is installed
docker compose exec ollama ollama list
```

**Solutions**:
```bash
# Restart Ollama
docker compose restart ollama

# Pull model if missing
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# Check network connectivity (inside app container)
docker compose exec app curl http://ollama:11434/api/tags
```

### Data Endpoints Return Errors

**Common Issues**:
- Invalid ticker symbol (e.g., typo)
- Data not available for that symbol
- yfinance API rate limiting

**Debugging**:
```bash
# Check app logs
docker compose logs app | grep ERROR

# Test directly
curl http://localhost:8000/api/fundamentals/AAPL

# Use interactive docs to see error details
open http://localhost:8000/docs
```

### Container Issues

```bash
# Check all containers
docker compose ps

# Restart all services
docker compose restart

# Rebuild app container
docker compose up -d --build app

# View all logs
docker compose logs
```

### Performance Issues

- **Slow AI responses**: Normal for CPU-only Ollama (30-60s for analysis)
- **Timeout errors**: Increase timeout in flow.py or use GPU-enabled Ollama
- **Memory issues**: Ollama requires ~4GB RAM for 3B parameter model

---

## Security Considerations

⚠️ **No Authentication**: This API does not include authentication or rate limiting

**Recommendations for Production**:
- Deploy behind a reverse proxy (nginx, Caddy)
- Add API key authentication
- Implement rate limiting
- Use HTTPS/TLS
- Restrict network access via firewall
- Monitor for abuse via logs

---

## Additional Resources

- **[README.md](README.md)**: Quick start and overview
- **[API_DEPLOYMENT_SUMMARY.md](API_DEPLOYMENT_SUMMARY.md)**: Complete deployment guide
- **[DOCKER.md](DOCKER.md)**: Docker-specific instructions
- **[TEST_RESULTS_SUMMARY.md](TEST_RESULTS_SUMMARY.md)**: Test results and coverage
- **[Swagger UI](http://localhost:8000/docs)**: Interactive API documentation
- **[ReDoc](http://localhost:8000/redoc)**: Alternative API reference
