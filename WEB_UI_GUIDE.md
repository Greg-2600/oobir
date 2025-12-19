# OOBIR Web UI Developer Guide

## Overview

The OOBIR Web UI is a modern, responsive stock analysis dashboard built with vanilla HTML5, CSS3, and JavaScript. It provides real-time stock data visualization, technical analysis charts, and on-demand AI-powered insights.

## Architecture

### Frontend Stack
- **HTML5**: Semantic markup and structure
- **CSS3**: Responsive grid layout with modern styling
- **JavaScript (Vanilla)**: No external dependencies—pure ES6+
- **Charting**: Custom candlestick chart implementation with canvas-free SVG-like rendering

### Key Design Principles
1. **No External Dependencies**: All functionality implemented in vanilla JS
2. **REST API Integration**: Communicates exclusively via FastAPI backend
3. **Client-Side Rendering**: All UI updates happen in the browser
4. **Progressive Enhancement**: Data loads progressively as needed
5. **On-Demand Analysis**: AI analysis buttons only load when clicked

## File Structure

```
web/
├── index.html       # Main HTML structure
├── styles.css       # Responsive styling (mobile-first)
├── app.js           # Frontend application logic
└── config.js        # Configuration (API base URL)
```

## Components

### index.html

**Landing Page Section**
```html
<div class="landing-page">
  - Logo and tagline
  - Search form for ticker input
  - Quick search suggestions
</div>
```

**Results Page Section**
```html
<div class="results-page">
  - Stock header with price
  - Featured price history card (candlestick chart)
  - Data grid with fundamentals, analyst targets, balance sheet, income statement, calendar
  - AI Analysis section with recommendation, technical analysis, news sentiment
</div>
```

### styles.css

**Layout System**
- CSS Grid for responsive multi-column layouts
- Mobile-first responsive design
- Card-based UI pattern for data grouping
- Flexbox for component alignment

**Key Classes**
- `.card` - Standard data container
- `.highlight-card` - Featured card (price history)
- `.data-grid` - Multi-column data layout
- `.text-success` / `.text-danger` - Color-coded text
- `.loading` - Loading state styling

### app.js

**Main Functions**

#### `initializeApp()`
- Sets up event listeners for search form
- Initializes page state

#### `handleSearch(ticker)`
- Validates ticker input
- Hides landing page, shows results page
- Initiates data loading cascade

#### `loadStockData(ticker)`
- Fetches all 6 data endpoints in parallel:
  1. Fundamentals
  2. Price history
  3. Analyst targets
  4. Calendar
  5. Income statement
  6. Balance sheet
- Handles errors gracefully
- Updates UI with loaded data

#### `renderPriceHistory(data, container)`
- **Most complex function** - renders candlestick chart with technical indicators
- Calculates SMA 20 and SMA 50
- Calculates Bollinger Bands (20-period, 2 std dev)
- Renders candlestick bodies and wicks
- Overlays indicator lines
- Displays legend and statistics

**Technical Indicator Calculation**
```javascript
calculateSMA(prices, period)         // Simple moving average
calculateBollingerBands(prices, period, stdDevMultiplier)  // BB bands
```

#### `initializeTechnicalAnalysis(ticker)`
- Creates "Run Analysis" button in technical-analysis-data container

#### `loadTechnicalAnalysis(ticker)`
- Fetches `/api/ai/technical-analysis/{ticker}`
- Renders response in results container

#### `initializeAIRecommendation(ticker)`
- Creates "Get Recommendation" button in ai-recommendation-data container

#### `loadAIRecommendation(ticker)`
- Fetches `/api/ai/action-recommendation/{ticker}`
- Renders response in results container

#### `initializeNewsSentiment(ticker)`
- Creates "Analyze Sentiment" button in news-sentiment-data container

#### `loadNewsSentiment(ticker)`
- Fetches `/api/ai/news-sentiment/{ticker}`
- Renders response in results container

#### `renderTable(fields, container)`
- Generic table rendering function
- Converts data objects to formatted HTML tables
- Handles different field types (currency, percent, etc.)

#### `formatCurrency(value)`
- Formats numbers as USD currency ($X.XX)

#### `formatPercent(value)`
- Formats decimals as percentages (X.XX%)

### config.js

```javascript
const API_BASE_URL = 'http://localhost:8000'; // Change for remote deployment
```

## API Integration

### Data Endpoints Used

**Auto-Loading Endpoints** (loaded on every search):
1. `/api/fundamentals/{ticker}` - Company metrics
2. `/api/price-history/{ticker}` - 120+ days OHLCV data
3. `/api/analyst-targets/{ticker}` - Price targets and recommendations
4. `/api/calendar/{ticker}` - Earnings and events
5. `/api/income-stmt/{ticker}` - Income statement data
6. `/api/balance-sheet/{ticker}` - Balance sheet data

**On-Demand AI Endpoints** (user clicks button):
1. `/api/ai/action-recommendation/{ticker}` - Detailed recommendation
2. `/api/ai/technical-analysis/{ticker}` - Technical pattern analysis
3. `/api/ai/news-sentiment/{ticker}` - News sentiment analysis

## Chart Implementation

### Candlestick Chart Rendering

The chart is rendered as nested HTML divs, not canvas or SVG:

```
Chart Container (flex row, 280px height)
├── Each Day Container (flex column, relative positioning)
│   ├── Bollinger Bands Background (absolute, transparent purple)
│   ├── SMA 50 Line (absolute, orange 1px)
│   ├── SMA 20 Line (absolute, blue 1px)
│   ├── Wick (absolute, 2px line showing High-Low)
│   └── Body (absolute, filled rectangle showing Open-Close)
```

### Technical Indicators

**SMA 20 (Simple Moving Average - 20 period)**
- Blue line
- Represents short-term trend
- Calculated: Average of closing prices over last 20 days

**SMA 50 (Simple Moving Average - 50 period)**
- Orange line
- Represents long-term trend
- Calculated: Average of closing prices over last 50 days

**Bollinger Bands**
- Purple shaded area
- Upper band: SMA(20) + (2 × Standard Deviation)
- Middle band: SMA(20)
- Lower band: SMA(20) - (2 × Standard Deviation)
- Indicates volatility and potential support/resistance levels

## Error Handling

### Network Errors
- Displays user-friendly messages
- Allows retry via search button
- Gracefully degrades (data that loaded is still shown)

### API Errors
- 404 errors: "Stock not found. Please check ticker symbol."
- 503/504 errors: "Service temporarily unavailable."
- Parse errors: Logs to console, shows generic error message

### Missing Data
- Missing chart data: Shows "No price history available"
- Missing balance sheet: Field is omitted from display
- Missing AI analysis: Button remains disabled with tooltip

## Performance Optimizations

1. **Parallel Data Loading**: All 6 data endpoints fetch simultaneously
2. **Client-Side Rendering**: All UI updates happen in browser (no server-side templating)
3. **No External Libraries**: Reduces download size and dependencies
4. **CSS Grid**: Native browser layout optimization
5. **Minimal DOM Manipulation**: Bulk updates via innerHTML where appropriate
6. **Request Deduplication**: AI endpoints only load when button clicked (not auto-loaded)

## Browser Compatibility

**Supported Browsers:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

**Features Used:**
- CSS Grid
- Fetch API
- Template Literals
- Arrow Functions
- Modern Event Listeners

## Customization Guide

### Changing Colors

Edit `app.js` in `renderPriceHistory()`:
```javascript
const chartHtml = `...
    <div><span style="background: #22c55e;"></span>Green = Up</div>  // Candle up color
    <div><span style="background: #ef4444;"></span>Red = Down</div>   // Candle down color
    <div><span style="background: #3b82f6;"></span>SMA 20</div>        // SMA20 color
    <div><span style="background: #f59e0b;"></span>SMA 50</div>        // SMA50 color
...`
```

Also update in the chart rendering section:
```javascript
const color = isUp ? '#22c55e' : '#ef4444';  // Candle color
// SMA lines in indicator HTML
'background: #f59e0b;'  // SMA50
'background: #3b82f6;'  // SMA20
```

### Changing Chart Height

Edit in `renderPriceHistory()`:
```javascript
style="height: 280px;"  // Change to desired height
```

### Adding New Data Fields

1. Add to HTML template in appropriate card
2. Add rendering logic in `renderTable()` or create custom render function
3. Verify field names match API response

### Connecting to Remote API

Edit `web/config.js`:
```javascript
const API_BASE_URL = 'http://192.168.1.248:8000'; // Your remote API URL
```

## Development Workflow

### Local Testing

```bash
# Terminal 1: Start API server
python flow_api.py

# Terminal 2: Serve web UI
cd web && python -m http.server 8081

# Browser: Open http://localhost:8081
```

### Docker Testing

```bash
docker compose up -d
# Web UI: http://localhost:8081
# API: http://localhost:8000
```

### Debugging

1. Open browser DevTools (F12)
2. Console tab shows debug logs
3. Network tab shows API calls
4. Elements tab shows DOM structure

## Testing

Web UI is tested via `tests/test_web_ui_integration.py`:

```bash
# Run Web UI integration tests
pytest tests/test_web_ui_integration.py -v

# Test categories:
# - API endpoint response formats
# - CORS headers for cross-origin requests
# - Data suitable for chart rendering
# - Error handling and edge cases
```

## Common Issues & Solutions

**Problem: API returns 403 Forbidden**
- Solution: Ensure API server is running and Nginx web server has proper mounts

**Problem: Chart doesn't render**
- Solution: Check browser console for JavaScript errors; verify price-history data format

**Problem: AI buttons don't work**
- Solution: Verify Ollama service is running and model is downloaded

**Problem: Slow data loading**
- Solution: Check network tab in DevTools; ensure API endpoints respond quickly

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Portfolio tracking with multiple stocks
- [ ] Custom technical indicator selection
- [ ] Export functionality (PDF reports, CSV)
- [ ] Dark mode
- [ ] Mobile app (React Native)
- [ ] Advanced charting (TradingView integration)
- [ ] Backtesting framework
- [ ] Machine learning predictions

---

**Last Updated**: December 19, 2025  
**Version**: 1.1.0
