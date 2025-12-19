# OOBIR Changelog

## [1.1.0] - 2024-12-19

### Added

#### Web UI Dashboard (Major Feature)
- **Interactive Stock Analysis Dashboard**
  - Real-time search with ticker symbol lookup
  - Responsive design optimized for desktop and tablet
  - Landing page with search interface
  - Results page with comprehensive financial data display

- **Candlestick Chart with Technical Indicators** (Professional Grade)
  - 120+ days of historical price data visualization
  - Candlestick rendering: green bodies for up days, red for down days
  - Wicks showing full trading range (High-Low)
  - **Technical Indicator Overlays:**
    - SMA 20 (blue line) - 20-period moving average for short-term trends
    - SMA 50 (orange line) - 50-period moving average for long-term trends
    - Bollinger Bands (purple shaded area) - 20-period with 2 standard deviations
  - Interactive tooltips showing OHLC data on hover
  - Chart height optimized for readability (280px)
  - Statistics display showing Latest Close, High, Low, SMA 20, SMA 50

- **Financial Data Display**
  - Fundamentals card: P/E ratio, market cap, earnings per share, dividend yield, ROE
  - Price history: Featured card with candlestick chart and technical indicators
  - Analyst targets: Consensus price targets and analyst recommendations
  - Balance sheet: Assets, liabilities, equity, cash
  - Income statement: Revenue, operating income, net income
  - Earnings calendar: Upcoming events and earnings dates

- **On-Demand AI Analysis Buttons**
  - AI Recommendation: Buy/sell/hold with detailed reasoning
  - Technical Analysis: AI interpretation of technical patterns and indicators
  - News & Sentiment: AI-powered sentiment analysis of recent news
  - Buttons only load when clicked (no slow auto-loading)
  - Results display below buttons after processing
  - Error handling with user-friendly messages

#### Documentation
- **README.md Updates**
  - Added Web UI section with usage instructions
  - Updated architecture diagrams to include Web UI layer
  - Added Web UI customization guide
  - Updated Quick Start with Web UI access information
  - Updated features section with Web UI capabilities
  - Updated Table of Contents

- **New WEB_UI_GUIDE.md** (Comprehensive Developer Guide)
  - Architecture overview and design principles
  - File structure and component documentation
  - Detailed function reference for all JavaScript functions
  - API integration guide with endpoint descriptions
  - Chart implementation details and technical indicators explanation
  - Error handling strategies
  - Performance optimizations
  - Browser compatibility information
  - Customization guide (colors, layout, chart height, remote API)
  - Development workflow for local and Docker testing
  - Debugging instructions
  - Future enhancement roadmap

- **New TESTING.md** (Complete Testing Documentation)
  - Test structure and organization
  - Running tests: all, by category, specific tests
  - Test coverage breakdown (56 total tests)
  - Data endpoint tests (13)
  - AI analysis endpoint tests (38)
  - Technical indicator tests (2)
  - Web UI integration tests (11 new tests)
  - Manual testing scripts documentation
  - Test mocking strategy and benefits
  - CI/CD pipeline recommendations
  - Coverage report generation
  - Troubleshooting guide
  - Best practices for writing tests
  - Performance and load testing guidance
  - Pre and post-deployment testing checklists

#### New Tests
- **tests/test_web_ui_integration.py** (11 new tests)
  - Tests for API response formats compatible with Web UI
  - Candlestick chart data format validation
  - Field name compatibility (PascalCase)
  - On-demand AI button endpoint compatibility
  - CORS headers verification
  - Error handling for Web UI
  - JSON serializability checks

### Changed

#### Code Updates
- **app.js** - Enhanced price history rendering
  - Added `calculateSMA(prices, period)` function for moving average calculation
  - Added `calculateBollingerBands(prices, period, stdDevMultiplier)` function
  - Enhanced `renderPriceHistory()` with technical indicator overlays
  - Improved chart height to 280px for better visibility
  - Added legend showing color coding for all indicators
  - Added statistics display with SMA values
  - Implemented client-side technical indicator calculation

- **index.html** - Layout reorganization
  - Moved price history to featured position (large highlight-card below stock header)
  - Reorganized data cards into grid (Fundamentals, Analyst Targets, Balance Sheet, Income Statement, Calendar)
  - Moved AI Analysis section to bottom with new "🧠 AI Analysis" header
  - Improved visual hierarchy with featured cards
  - Updated cache busting version from v=4 to v=7

- **styles.css** - Added Web UI styling
  - Responsive grid layouts for multi-column data display
  - Card-based design system
  - Mobile-first responsive design
  - Color-coded text for positive/negative changes
  - Loading states and error styling

- **flow_api.py** - CORS configuration
  - Added CORSMiddleware configuration for cross-origin requests from Web UI
  - Configured allowed origins, methods, headers for Web UI access

- **README.md** - Comprehensive updates
  - Updated badge for HTML5 support
  - Updated version to 1.1.0
  - Updated status to "Production Ready with Interactive Web UI"
  - Added Web UI features section with screenshots/descriptions
  - Updated architecture section with Web UI layer
  - Added Web UI usage instructions
  - Updated Quick Start for Web UI access
  - Updated Table of Contents

### Fixed

#### Bug Fixes
- **Template Literal Escaping Issue** (Critical)
  - Fixed nested backticks in chart rendering that were breaking template string
  - Converted template literal for chart indicators to string concatenation
  - Chart now properly renders SMA lines and Bollinger Bands

- **JSON Parsing Consistency**
  - Ensured all data endpoints properly parse JSON strings to objects before returning
  - Fixed double-stringified JSON issues across all endpoints

- **Cache Busting**
  - Implemented versioning system for JavaScript and CSS (v=7)
  - Ensures browsers load latest code after updates

### Performance Improvements
- Client-side technical indicator calculation (no server-side overhead)
- Parallel loading of all 6 data endpoints simultaneously
- No external JavaScript dependencies (faster load times)
- CSS Grid for native browser layout optimization
- On-demand AI loading (no unnecessary API calls)

### Testing Improvements
- Added 11 new Web UI integration tests
- Total test count increased from 45 to 56 tests
- Added CORS header validation tests
- Added JSON serializability tests
- Added error handling tests for Web UI scenarios

### Documentation Improvements
- Added 2 new comprehensive guides (WEB_UI_GUIDE.md, TESTING.md)
- Updated README with 30+ lines of Web UI documentation
- Added API endpoint descriptions for Web UI usage
- Added customization guide for Web UI
- Added development workflow documentation
- Added test coverage breakdown and examples
- Added troubleshooting guides for common issues

## [1.0.0] - 2024-12-18

### Initial Release

#### Core Features
- FastAPI REST API with 24 endpoints
- CLI interface via flow.py
- Ollama LLM integration for AI analysis
- yfinance data integration
- Docker/Docker Compose deployment
- Comprehensive test suite (45 tests)
- Health monitoring for app and Ollama

#### API Endpoints (24 total)
- 2 Health check endpoints
- 13 Data retrieval endpoints
- 9 AI analysis endpoints

#### Database & Data
- Real-time stock data via yfinance
- Fundamental metrics
- Historical price data (120+ days)
- Analyst targets and consensus
- Balance sheet and income statement
- Earnings calendar
- News articles
- Options chain data
- Stock screening

#### AI Analysis
- LLM-powered fundamental analysis
- Technical analysis
- Balance sheet analysis
- Income statement analysis
- Action recommendations (detailed, sentence, word)
- News sentiment analysis
- Full report generation

#### Documentation
- README.md with comprehensive guide
- API endpoint documentation
- Installation instructions
- Docker deployment guide
- Contributing guidelines

#### Testing
- 45 unit tests
- 100% endpoint coverage
- External service mocking
- Error path testing

---

## Migration Guide (v1.0 → v1.1)

### For Users

1. **Web UI Access**
   - Old: Only REST API available
   - New: Access Web UI at `http://localhost:8081` (Docker) or `http://localhost:8081` (local)

2. **Browser**
   - No breaking changes to REST API
   - Existing API clients continue to work
   - New Web UI provides easier stock analysis

3. **Deployment**
   - Docker Compose now includes web service
   - `docker compose up -d` deploys both API and Web UI
   - Web UI served by Nginx on port 8081

### For Developers

1. **New Test File**
   - Add `tests/test_web_ui_integration.py` to your test suite
   - Run `pytest tests/test_web_ui_integration.py` for Web UI tests

2. **Web UI Customization**
   - Reference `WEB_UI_GUIDE.md` for customization options
   - Edit `web/config.js` to change API base URL
   - Edit `web/styles.css` for styling changes

3. **Documentation**
   - Read `WEB_UI_GUIDE.md` for Web UI architecture
   - Read `TESTING.md` for comprehensive testing guide
   - Updated `README.md` has Web UI section

4. **CI/CD**
   - Add Web UI integration tests to CI pipeline
   - Example: `pytest tests/ -v` includes new tests
   - Web assets must be deployed to Nginx container

---

**Release Date**: December 19, 2025  
**Release Type**: Feature Release (Major)  
**Breaking Changes**: None
