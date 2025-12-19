# OOBIR Testing Documentation

## Overview

OOBIR includes a comprehensive test suite with **56 tests** covering:
- 13 data endpoints
- 9 AI analysis endpoints  
- 3 technical indicator functions
- 11 Web UI integration scenarios
- CORS headers and error handling

## Test Structure

```
tests/
├── test_data_endpoints.py           # 13 tests for data retrieval
├── test_ai_analysis_endpoints.py    # 38 tests for AI features
├── test_technical_indicators.py     # 2 tests for indicator calculations
├── test_web_ui_integration.py       # NEW: 11 tests for Web UI compatibility
└── scripts/
    ├── test_data_endpoints.sh       # Manual cURL script for data testing
    ├── test_ai_endpoints.sh         # Manual cURL script for AI testing
    └── test_remote_api_comprehensive.sh  # Full remote API testing
```

## Running Tests

### All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=flow --cov=flow_api --cov-report=html

# Run in Docker
docker compose exec app pytest tests/ -v
```

### By Category

```bash
# Data endpoints only
pytest tests/test_data_endpoints.py -v

# AI analysis endpoints only
pytest tests/test_ai_analysis_endpoints.py -v

# Technical indicators only
pytest tests/test_technical_indicators.py -v

# Web UI integration only (NEW)
pytest tests/test_web_ui_integration.py -v
```

### Specific Test

```bash
# Run single test function
pytest tests/test_data_endpoints.py::TestDataEndpoints::test_health_endpoint -v

# Run tests matching pattern
pytest -k "fundamentals" -v
```

## Test Coverage

### Data Endpoints (13 tests)

**test_data_endpoints.py**

| Test | Endpoint | Purpose |
|------|----------|---------|
| `test_health_endpoint` | GET /health | Verify app is running |
| `test_ollama_health_endpoint` | GET /health/ollama | Verify Ollama service health |
| `test_fundamentals_endpoint` | GET /api/fundamentals/{symbol} | Company metrics retrieval |
| `test_price_history_endpoint` | GET /api/price-history/{symbol} | Historical price data |
| `test_analyst_targets_endpoint` | GET /api/analyst-targets/{symbol} | Price targets & consensus |
| `test_calendar_endpoint` | GET /api/calendar/{symbol} | Earnings dates & events |
| `test_balance_sheet_endpoint` | GET /api/balance-sheet/{symbol} | Balance sheet data |
| `test_income_stmt_endpoint` | GET /api/income-stmt/{symbol} | Income statement data |
| `test_option_chain_endpoint` | GET /api/option-chain/{symbol} | Options chain data |
| `test_news_endpoint` | GET /api/news/{symbol} | News articles |
| `test_screen_undervalued_endpoint` | GET /api/screen-undervalued | Stock screener |
| `test_invalid_ticker_404` | GET /api/fundamentals/{invalid} | Error handling |
| `test_nonexistent_endpoint_404` | GET /api/nonexistent | 404 response |

### AI Analysis Endpoints (38 tests)

**test_ai_analysis_endpoints.py**

| Feature | Endpoint | Tests |
|---------|----------|-------|
| Fundamental Analysis | `/api/ai/fundamental-analysis/{symbol}` | 2 |
| Balance Sheet Analysis | `/api/ai/balance-sheet-analysis/{symbol}` | 2 |
| Income Statement Analysis | `/api/ai/income-stmt-analysis/{symbol}` | 2 |
| Technical Analysis | `/api/ai/technical-analysis/{symbol}` | 2 |
| Action Recommendation | `/api/ai/action-recommendation/{symbol}` | 2 |
| Action Rec. Sentence | `/api/ai/action-recommendation-sentence/{symbol}` | 2 |
| Action Rec. Word | `/api/ai/action-recommendation-word/{symbol}` | 2 |
| News Sentiment | `/api/ai/news-sentiment/{symbol}` | 2 |
| Full Report | `/api/ai/full-report/{symbol}` | 2 |
| Ollama Error Handling | Various AI endpoints | 18 |

Each endpoint tested for:
- ✅ Success case (200 response with valid data)
- ❌ Error case (503 when service unavailable)

### Technical Indicators (2 tests)

**test_technical_indicators.py**

| Test | Purpose |
|------|---------|
| `test_calculate_technical_indicators_contains_expected_sections` | Verify SMA, RSI, MACD, Bollinger Bands are calculated |
| `test_ai_technical_analysis_includes_indicators` | Verify indicators are sent to LLM for analysis |

### Web UI Integration (11 tests)

**test_web_ui_integration.py** (NEW)

| Test | Purpose |
|------|---------|
| `test_fundamentals_endpoint_returns_json_serializable` | JSON format for Web UI display |
| `test_price_history_endpoint_format_for_candlestick_chart` | Format compatible with chart rendering |
| `test_analyst_targets_endpoint_format` | Analyst data structure |
| `test_calendar_endpoint_format` | Calendar data structure |
| `test_balance_sheet_endpoint_field_names_for_ui` | PascalCase field name compatibility |
| `test_income_statement_endpoint_format` | Income statement structure |
| `test_ai_recommendation_endpoint_for_ui_button` | AI rec. button compatibility |
| `test_technical_analysis_endpoint_for_ui_button` | Technical analysis button compatibility |
| `test_news_sentiment_endpoint_for_ui_button` | News sentiment button compatibility |
| `test_cors_headers_allow_cross_origin` | CORS headers enabled |
| `test_fundamentals_endpoint_returns_valid_json` | JSON serializability |
| `test_invalid_ticker_returns_error` | Error handling for Web UI |
| `test_ai_endpoint_error_handling` | AI service error handling |

## Test Execution Examples

### Development Testing (Local)

```bash
# Run all tests after making changes
pytest tests/ -v --tb=short

# Run and show coverage
pytest tests/ --cov=flow --cov=flow_api --cov-report=term-missing

# Run specific test
pytest tests/test_web_ui_integration.py::TestWebUIDataEndpoints::test_price_history_endpoint_format_for_candlestick_chart -v
```

### Docker Testing

```bash
# Run in container
docker compose exec app pytest tests/ -v

# Run specific test in container
docker compose exec app pytest tests/test_ai_analysis_endpoints.py::TestAIAnalysisEndpoints::test_fundamental_analysis_endpoint -v

# Generate coverage in container
docker compose exec app pytest tests/ --cov=flow --cov=flow_api --cov-report=html
```

### CI/CD Testing (Pre-Deployment)

```bash
# Full validation before deployment
pytest tests/ -v --tb=short && \
pytest tests/ --cov=flow --cov=flow_api --cov-report=term && \
echo "All tests passed! Safe to deploy."
```

## Manual Testing Scripts

### Data Endpoints Script

```bash
./tests/scripts/test_data_endpoints.sh [BASE_URL] [SYMBOL]

# Examples:
./tests/scripts/test_data_endpoints.sh http://localhost:8000 AAPL
./tests/scripts/test_data_endpoints.sh http://192.168.1.248:8000 MSFT
./tests/scripts/test_data_endpoints.sh  # Uses defaults
```

Output: Tests all data endpoints, shows response times and HTTP status codes

### AI Endpoints Script

```bash
./tests/scripts/test_ai_endpoints.sh [BASE_URL] [SYMBOL]

# Examples:
./tests/scripts/test_ai_endpoints.sh http://localhost:8000 AAPL
./tests/scripts/test_ai_endpoints.sh http://192.168.1.248:8000 TSLA
```

Output: Tests all AI endpoints, shows JSON responses from LLM

### Comprehensive Remote Testing

```bash
./tests/scripts/test_remote_api_comprehensive.sh <user@host>

# Example:
./tests/scripts/test_remote_api_comprehensive.sh greg@192.168.1.248

# Includes:
# - Health checks
# - All data endpoint responses
# - All AI endpoint responses
# - Performance metrics
# - Error scenarios
```

## Test Mocking Strategy

### External Service Mocking

All tests mock external services to ensure reliability without dependencies:

**yfinance Mocking** (data endpoints)
```python
@patch('flow.get_fundamentals')
def test_fundamentals(self, mock_get_fundamentals):
    mock_get_fundamentals.return_value = {'pe_ratio': 25.5, ...}
    # Test doesn't require real yfinance API
```

**Ollama Mocking** (AI endpoints)
```python
@patch('flow.ensure_ollama')
@patch('flow.get_ai_fundamental_analysis')
def test_ai_fundamental(self, mock_analysis, mock_ollama):
    mock_analysis.return_value = 'Strong fundamentals...'
    # Test doesn't require real Ollama service
```

### Benefits of Mocking
- ✅ Tests run fast (no network calls)
- ✅ Reliable (no external service failures)
- ✅ Isolated (each test is independent)
- ✅ Predictable (deterministic responses)

## Continuous Integration

### GitHub Actions (Recommended)

`.github/workflows/tests.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r dev-requirements.txt
      - run: pytest tests/ -v --tb=short
      - run: pytest tests/ --cov=flow --cov=flow_api --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Pre-Commit Hook

`.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest tests/ -v --tb=short || exit 1
```

Enable with:
```bash
chmod +x .git/hooks/pre-commit
```

## Coverage Reports

### Generate Coverage Report

```bash
# Terminal output
pytest tests/ --cov=flow --cov=flow_api --cov-report=term-missing

# HTML report
pytest tests/ --cov=flow --cov=flow_api --cov-report=html
# Open htmlcov/index.html in browser

# Coverage target
pytest tests/ --cov=flow --cov=flow_api --cov-report=term --cov-fail-under=90
```

### Coverage by Module

| Module | Coverage | Tests |
|--------|----------|-------|
| flow.py (business logic) | 95%+ | 51 |
| flow_api.py (REST API) | 95%+ | 5 |
| app.js (Web UI) | Manual | Web integration tests |

## Troubleshooting Tests

### Test Failures

**Problem: ImportError for flow module**
```bash
# Solution: Ensure you're in project root
cd /Users/greg/oobir
source venv/bin/activate
pytest tests/
```

**Problem: Mock not working**
```bash
# Solution: Verify patch path matches actual module import
# In test: @patch('flow.get_fundamentals')
# Verify flow_api imports: from flow import get_fundamentals
```

**Problem: CORS errors in Web UI tests**
```bash
# Solution: API should have CORS middleware enabled
# In flow_api.py: app.add_middleware(CORSMiddleware, ...)
```

**Problem: Ollama tests failing**
```bash
# Ollama might not be running - but tests should mock it
# Check @patch decorators are applied
# Run: pytest tests/test_ai_analysis_endpoints.py -vv --tb=long
```

### Debugging Tests

```bash
# Verbose output with full tracebacks
pytest tests/ -vv --tb=long

# Show print statements and logging
pytest tests/ -s

# Run single test with debugging
pytest tests/test_data_endpoints.py::TestDataEndpoints::test_health_endpoint -vv -s

# Enable Python debugger on failure
pytest tests/ --pdb
```

## Best Practices

### Writing New Tests

1. **Use Mocking** - Never make real API calls in tests
```python
@patch('flow.get_fundamentals')
def test_my_feature(self, mock_get_fundamentals):
    mock_get_fundamentals.return_value = {'symbol': 'TEST', ...}
```

2. **Test Both Success and Error Cases**
```python
def test_success_case(self, mock_func):
    mock_func.return_value = valid_data
    # assert success

def test_error_case(self, mock_func):
    mock_func.return_value = None
    # assert error handling
```

3. **Use Descriptive Names**
```python
# Good
def test_fundamentals_endpoint_returns_pe_ratio(self):

# Bad
def test_endpoint(self):
```

4. **Document Expectations**
```python
def test_price_history_format(self):
    """Test price history returns format: {data: [{Date, Open, High, Low, Close}]}"""
```

### Test Organization

- Group related tests in classes (`TestDataEndpoints`, `TestAIAnalysisEndpoints`)
- Use setUp() for common initialization
- Use meaningful assertions with messages

```python
class TestPriceHistory(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(flow_api.app)
    
    def test_format(self):
        # Test with clear intent
        self.assertIn('data', response.json(), 'Price history must contain data key')
```

## Performance Testing

### Response Time Testing

```bash
# Measure API response times
time curl http://localhost:8000/api/fundamentals/AAPL

# Measure in Docker
docker compose exec app time curl http://localhost:8000/api/fundamentals/AAPL
```

### Load Testing (Future)

```bash
# Install: pip install locust
locust -f tests/load_tests.py --host=http://localhost:8000
```

## Production Testing

### Before Deployment

```bash
# Full validation suite
./tests/scripts/test_remote_api_comprehensive.sh user@production-server

# Verify all endpoints
pytest tests/ -v --tb=short

# Check coverage
pytest tests/ --cov=flow --cov=flow_api --cov-report=term-missing | grep -E "^(TOTAL|tests/)"
```

### Post-Deployment

```bash
# Smoke test (verify basic functionality)
curl http://production-server:8000/health
curl http://production-server:8000/api/fundamentals/AAPL
curl http://production-server:8000/api/ai/technical-analysis/AAPL

# Check Web UI
curl http://production-server:8081/
```

## Test Maintenance

### Regular Updates

- Update tests when API contract changes
- Add tests for new features (before implementation)
- Remove tests for deprecated features
- Review and refactor test code quarterly

### Test Documentation

- Keep test docstrings updated
- Document complex test scenarios
- Record known flaky tests and workarounds
- Maintain this README as you add new tests

---

**Last Updated**: December 19, 2025  
**Version**: 1.1.0  
**Test Count**: 56 tests (13 data + 38 AI + 2 indicators + 11 Web UI + CORS + error handling)
