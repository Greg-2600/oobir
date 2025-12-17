# OOBIR API Test Results Summary

**Test Date:** December 16, 2025
**Target:** http://192.168.1.248:8000 (remote)

## Deployment Status

✅ **Deployment Complete**
- Code changes applied to `flow.py` and `flow_api.py`
- Updated `docker-compose.yml` with `OLLAMA_CONTEXT_SIZE=32000`
- Remote containers redeployed via `deploy_remote.sh`

## Test Configuration

- **Shell Scripts:** `test_data_endpoints.sh`, `test_ai_endpoints.sh`
- **Timeout for Data Endpoints:** ~30 seconds typical
- **Timeout for AI Endpoints:** Up to 480 seconds (8 minutes)

## Previous Test Run Results (Before Fixes)

### Curl Tests Against http://192.168.1.248:8000

**Metadata (4/4 passing):**
```
✓ / → 200
✓ /docs → 200
✓ /redoc → 200
✓ /openapi.json → 200
```

**Data Endpoints (2/9 passing):**
```
✓ /api/fundamentals/CHTR → 200
✓ /api/price-history/CHTR → 200
✗ /api/analyst-targets/CHTR → 500 (function name mismatch)
✗ /api/calendar/CHTR → 500 (JSON serialization error)
✗ /api/income-stmt/CHTR → 500 (DataFrame not JSON serializable)
✗ /api/balance-sheet/CHTR → 500 (DataFrame not JSON serializable)
✗ /api/option-chain/CHTR → 500 (DataFrame not JSON serializable)
✓ /api/news/CHTR → 200
✓ /api/screen-undervalued → 200
```

**AI Endpoints (8/8 passing):**
```
✓ /api/ai/fundamental-analysis/CHTR → 200
✓ /api/ai/balance-sheet-analysis/CHTR → 200
✓ /api/ai/income-stmt-analysis/CHTR → 200
✓ /api/ai/technical-analysis/CHTR → 200
✓ /api/ai/action-recommendation/CHTR → 200
✓ /api/ai/action-recommendation-sentence/CHTR → 200
✓ /api/ai/action-recommendation-word/CHTR → 200
✓ /api/ai/full-report/CHTR → 200
```

## Code Changes Applied

### 1. `/Users/greg/oobir/oobir/flow.py`

Added import for `date` and `datetime`, and made the following functions return JSON-serializable data:

- **`get_analyst_price_targets()`** - Convert result to dict
- **`get_calendar()`** - Call `.to_dict()` on calendar object, fallback to ISO format for dates
- **`get_quarterly_income_stmt()`** - Call `.to_dict()` on DataFrame
- **`get_option_chain()`** - Call `.to_dict()` on DataFrame, fallback to list of dicts
- **`get_balance_sheet()`** - Call `.to_dict()` on DataFrame

### 2. `/Users/greg/oobir/oobir/flow_api.py`

**Fixed function name mismatch in `/api/analyst-targets/{symbol}` endpoint:**

```python
# BEFORE:
result = flow.get_analyst_price_targets_and_calendar(symbol)

# AFTER:
result = flow.get_analyst_price_targets(symbol)
```

### 3. `/Users/greg/oobir/oobir/docker-compose.yml`

Added Ollama context configuration:

```yaml
ollama:
  environment:
    - OLLAMA_ALLOW_HTTP=true
    - OLLAMA_CONTEXT_SIZE=32000  # New: increase model context window
```

### Shell Test Scripts

Use the provided shell scripts for quick verification of endpoints using `curl`:

- `test_data_endpoints.sh` – checks metadata and data endpoints
- `test_ai_endpoints.sh` – checks AI analysis/recommendation endpoints

## How to Run the Full Test Suite

### From Local Machine

```bash
# Fast data tests
./test_data_endpoints.sh http://192.168.1.248:8000 AAPL

# AI tests (slower)
./test_ai_endpoints.sh http://192.168.1.248:8000 AAPL
```

### On Remote Server

```bash
ssh greg@192.168.1.248
cd /home/greg/oobir

# Check containers are running
docker compose ps

# View app logs
docker compose logs app

# Run tests from the repo directory on the server
./test_data_endpoints.sh http://localhost:8000 AAPL
./test_ai_endpoints.sh http://localhost:8000 AAPL
```

## Expected Test Duration

- **Data endpoints (4 metadata + 5 data):** ~5-10 seconds
- **AI endpoints (8 endpoints):** Up to 8 minutes per endpoint
- **Total full suite:** ~60+ minutes (if all AI endpoints complete)

## Notes on AI Endpoint Latency

The AI endpoints use Ollama with the `huihui_ai/llama3.2-abliterate:3b` model, which:
- Takes time to load the model if not in memory
- Generates responses based on complex financial data
- Can take 2-8 minutes per request depending on data size and server load

**Recommendation:** Run data tests first for quick feedback, then run AI tests separately if needed.

## Troubleshooting

If endpoints return 500 errors:

1. Check remote container logs:
   ```bash
   ssh greg@192.168.1.248 "cd /home/greg/oobir && docker compose logs app | tail -50"
   ```

2. Verify containers are running:
   ```bash
   ssh greg@192.168.1.248 "cd /home/greg/oobir && docker compose ps"
   ```

3. Redeploy if needed:
   ```bash
   ./deploy_remote.sh greg@192.168.1.248 /home/greg/oobir
   ```

## Next Steps

1. Run the full test suite with the updated code
2. Allow 60+ minutes for completion (due to AI endpoint latency)
3. Collect results and verify all endpoints return 200
4. Monitor remote logs to ensure no errors occur during processing
