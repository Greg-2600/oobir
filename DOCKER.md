# Running a local Ollama container (for `flow.py`)

This document shows a minimal Docker Compose setup to run a local Ollama service and how to point `flow.py` at it.

Start the Ollama container:

```bash
docker-compose up -d
```

Watch logs while it starts (optional):

```bash
docker-compose logs -f ollama
```

When the container is healthy and listening on host port `11435` (container port 11434), activate your virtualenv and run `flow.py` pointing to the local host:

```bash
. venv/bin/activate
python flow.py --host http://localhost:11435 AAPL get_ai_fundamental_analysis
```

Notes:
- The Compose file uses the image `ollama/ollama:latest`; if your environment requires a different image or tag, update `docker-compose.yml`.
- Models and state are persisted to the `ollama_data` volume defined in `docker-compose.yml`.
- If you previously hit the `librtmp` error when running `flow.py`, that only affected `yfinance`'s transport native libs. Running Ollama in Docker isolates the Ollama service; you may still need to ensure your Python environment can import required packages (install system deps or use mocked tests).

Model installation
------------------

Ollama requires models to be installed before you can run AI calls. After the container is running, pull the model used by this project:

```bash
# from the host where the container runs (uses compose plugin if available)
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b || docker exec -i ollama ollama pull huihui_ai/llama3.2-abliterate:3b
```

You can verify installed models with:

```bash
docker compose exec ollama ollama list || docker exec -i ollama ollama list
```

Run everything inside container
------------------------------

This repository includes an `app` service that builds a container image containing the project and its Python dependencies. The app container runs on the same docker network as the Ollama service so it can call `http://ollama:11434`.

Build and start both services:

```bash
docker compose up -d --build
```

The app container now runs a FastAPI server by default on port 8000. It will be accessible at `http://localhost:8000`.

Keep the containers running and then execute tests or interact with the app inside the `app` container:

```bash
# run tests inside the app container
docker compose exec app /home/app/oobir/run-tests.sh

# open a shell inside the app container
docker compose exec app bash

# run the CLI inside the container (example):
python flow.py --host http://ollama:11434 AAPL get_ai_fundamental_analysis

# access the FastAPI interactive documentation
open http://localhost:8000/docs         # Swagger UI
open http://localhost:8000/redoc        # ReDoc
```

REST API via Docker
-------------------

The `app` container exposes a FastAPI REST API on port 8000 with the following endpoints:

**Metadata Endpoints**:
- `GET /` — API info and current Ollama host
- `GET /docs` — Interactive Swagger UI documentation
- `GET /redoc` — ReDoc alternative documentation

**Health Check Endpoints**:
- `GET /health` — Basic service health check
- `GET /health/ollama` — Ollama connectivity test (returns 503 if unreachable)

**Data Endpoints** (GET):
- `/api/fundamentals/{symbol}` — Get fundamental data for a ticker
- `/api/price-history/{symbol}` — Get price history for a ticker
- `/api/analyst-targets/{symbol}` — Get analyst targets for a ticker
- `/api/calendar/{symbol}` — Get earnings calendar for a ticker
- `/api/income-stmt/{symbol}` — Get income statement for a ticker
- `/api/balance-sheet/{symbol}` — Get balance sheet for a ticker
- `/api/option-chain/{symbol}` — Get option chain for a ticker
- `/api/news/{symbol}` — Get news for a ticker
- `/api/screen-undervalued` — Screen for undervalued stocks

**AI Analysis Endpoints** (GET):
- `/api/ai/fundamental-analysis/{symbol}` — AI analysis of fundamentals
- `/api/ai/balance-sheet-analysis/{symbol}` — AI analysis of balance sheet
- `/api/ai/income-stmt-analysis/{symbol}` — AI analysis of income statement
- `/api/ai/technical-analysis/{symbol}` — AI technical analysis
- `/api/ai/action-recommendation/{symbol}` — AI action recommendation (JSON)
- `/api/ai/action-recommendation-sentence/{symbol}` — AI recommendation (sentence)
- `/api/ai/action-recommendation-word/{symbol}` — AI recommendation (one word)
- `/api/ai/full-report/{symbol}` — Complete AI analysis report

**Note:** All AI endpoints return HTTP 503 (Service Unavailable) if Ollama is unreachable or returns no response. Use `/health/ollama` to verify Ollama connectivity before making AI requests.

Example API calls:

```bash
# Check API and Ollama health
curl http://localhost:8000/health
curl http://localhost:8000/health/ollama

# Get fundamentals for AAPL via local Docker API
curl http://localhost:8000/api/fundamentals/AAPL

# Get AI action recommendation for AAPL
curl http://localhost:8000/api/ai/action-recommendation/AAPL

# Check API metadata
curl http://localhost:8000/
```

Testing the API
---------------

A standalone test script `test_apis.py` is included to verify all endpoints. Run it against a local or remote API:

```bash
# Test local Docker API
python test_apis.py http://localhost:8000

# Test remote API (after deploying to remote host)
python test_apis.py http://192.168.1.248:8000
```

The script tests all 23 endpoints (4 metadata + 2 health + 9 data including screener + 8 AI) and reports results with a summary.


