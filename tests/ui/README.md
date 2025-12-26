# Selenium UI Tests for OOBIR

Comprehensive browser automation tests for the OOBIR web UI using Selenium with pytest.

## Features

- **Multi-browser support**: Chrome and Firefox (easily extensible to Safari)
- **Pytest integration**: Test discovery, fixtures, parametrization
- **WebDriver management**: Automatic driver download via webdriver-manager
- **Comprehensive test coverage**:
  - Page load and element visibility
  - Stock search functionality
  - Results display and data tables
  - AI recommendations
  - Tab switching and navigation
  - Error handling

## Test Categories

### HomePageLoad
- Page loads with correct title
- Landing page and key elements visible
- Search button clickable
- Tagline present

### StockSearch
- Search with valid ticker (AAPL, MSFT, etc.)
- Input accepts text
- Case-insensitive search
- Empty search prevention

### ResultsPageDisplay
- Company info displays
- Stock header shows
- Back button works
- Tab navigation visible

### RecommendationsSection
- Recommendations load
- Action displays (BUY/SELL/HOLD)
- Recommendation cards visible

### DataTables
- Fundamentals table loads
- Price history displays
- Table rows populate

### UIInteractions
- Logo click returns home
- Enter key submits search
- Tab switching works

### ErrorHandling
- Invalid ticker handling
- Special character sanitization

## Installation

```bash
pip install selenium pytest webdriver-manager
```

## Running Tests

### Run all UI tests:
```bash
pytest tests/ui/ -v
```

### Run specific test class:
```bash
pytest tests/ui/test_ui.py::TestStockSearch -v
```

### Run specific test:
```bash
pytest tests/ui/test_ui.py::TestStockSearch::test_search_with_valid_ticker -v
```

### Run with headless mode (CI/CD):
Edit `conftest.py` and uncomment the `--headless` lines

### Run with custom base URL:
```bash
BASE_URL=http://192.168.1.175:8082 pytest tests/ui/ -v
```

### Run with custom timeout:
```bash
WAIT_TIMEOUT=15 pytest tests/ui/ -v
```

## Configuration

Environment variables:
- `BASE_URL`: Application URL (default: http://localhost:8081)
- `WAIT_TIMEOUT`: Selenium wait timeout in seconds (default: 10)

## Browser Parameterization

Tests automatically run against both Chrome and Firefox. To run only one browser:

```bash
pytest tests/ui/ -k "chrome" -v  # Chrome only
pytest tests/ui/ -k "firefox" -v  # Firefox only
```

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
- name: Run Selenium UI Tests
  env:
    BASE_URL: ${{ secrets.TEST_URL }}
  run: |
    pip install selenium pytest webdriver-manager
    pytest tests/ui/ -v --tb=short
```

## Requirements

- Python 3.9+
- Chrome/Firefox browsers installed
- Selenium 4.x
- pytest
- webdriver-manager
