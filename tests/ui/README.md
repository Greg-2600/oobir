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
  - Exploration and related-stock discovery flows
  - Since-last-view badges and revisit marker toggles
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

### EnhancedNavigationUX
- Section chip scrolling and active state
- Since-last-view revisit badge rendering
- Badge tooltip explanation text
- Revisit marker toggle hide/show behavior

## Installation

```bash
pip install selenium pytest webdriver-manager
```

## Running Tests

### Run all UI tests:
```bash
pytest tests/ui/ -v
```

### Run full UI exercise suite (all pages + exploration flow):
```bash
pytest tests/ui/ -v -k "UnifiedTopHeader or RelatedStocksExplorer or HomePageLoad or StockSearch or ResultsPageDisplay"
```

### Run specific test class:
```bash
pytest tests/ui/test_ui.py::TestStockSearch -v
```

### Run specific test:
```bash
pytest tests/ui/test_ui.py::TestStockSearch::test_search_with_valid_ticker -v
```

### Run with headless mode (CI/CD style):
```bash
HEADLESS=1 UI_BROWSERS=chrome pytest tests/ui/ -v
```

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
- `WAIT_TIMEOUT`: Selenium wait timeout in seconds (default: 20)
- `SELENIUM_REMOTE_URL`: Optional remote WebDriver endpoint (for Selenium Grid/Selenoid), e.g. `http://localhost:4444/wd/hub`
- `UI_BROWSERS`: Comma-separated browser list (default: `chrome`)
- `HEADLESS`: `1` for headless (default), `0` for headed

### Example using Selenium Grid
```bash
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub \
BASE_URL=http://localhost:8081 \
UI_BROWSERS=chrome,firefox \
pytest tests/ui/ -v
```

## Browser Parameterization

Tests automatically run against both Chrome and Firefox. To run only one browser:

```bash
pytest tests/ui/ -k "chrome" -v  # Chrome only
pytest tests/ui/ -k "firefox" -v  # Firefox only
```

## CI/CD Integration

This repository includes a ready-to-use GitHub Actions workflow:

- `.github/workflows/ui-selenium.yml`
- Builds/starts API + web services in CI
- Runs targeted smoke tests for critical UI journeys

Smoke tests currently gated in CI:

```bash
python -m pytest \
  tests/ui/test_ui.py::TestEnhancedNavigationUX::test_since_last_view_badge_updates_after_revisit \
  tests/ui/test_ui.py::TestEnhancedNavigationUX::test_revisit_marker_toggle_hides_and_shows_related_markers \
  -q --maxfail=1 --tb=short
```

If you need a custom pipeline, use this minimal example:

```yaml
- name: Run Selenium UI Tests
  env:
    BASE_URL: http://127.0.0.1:8081
    UI_BROWSERS: chrome
    HEADLESS: "1"
    WAIT_TIMEOUT: "30"
  run: |
    pip install selenium pytest webdriver-manager
    pytest tests/ui/test_ui.py::TestEnhancedNavigationUX::test_since_last_view_badge_updates_after_revisit -q --tb=short
```

## Requirements

- Python 3.9+
- Chrome/Firefox browsers installed
- Selenium 4.x
- pytest
- webdriver-manager
