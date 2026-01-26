# OOBIR — AI-Powered Stock Analysis Platform

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/REST_API-FastAPI-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Cloud_Native-Docker-blue?logo=docker)
![AI](https://img.shields.io/badge/AI-Ollama_LLM-purple?logo=ai)
![HTML5](https://img.shields.io/badge/Web_UI-HTML5_CSS3_JS-orange?logo=html5)
![Tests](https://img.shields.io/badge/Tests-66_Passing-brightgreen)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

> **Enterprise-grade stock analysis combining REST APIs, AI-powered insights, technical & fundamental analysis in a cloud-native architecture**

## 🚀 What is OOBIR?

**OOBIR** is a production-ready **REST API-first stock analysis platform** powered by artificial intelligence and built with modern cloud-native architecture. Developed in **Python** with **FastAPI**, containerized with **Docker**, and enhanced by **Ollama LLM**, OOBIR delivers comprehensive stock market intelligence through both **fundamental** and **technical analysis** approaches.

**Key Differentiators:**
- 🔌 **REST API First**: 25 production-ready endpoints (13 data + 10 AI + 1 strategy + 2 health) with auto-generated OpenAPI docs
- 🤖 **AI-Powered**: Local Ollama LLM (Llama 3.2) for privacy-preserving intelligent analysis
- ☁️ **Cloud-Native**: Docker containerization for deployment anywhere (AWS, Azure, GCP, on-premises)
- 🐍 **Python-Driven**: Modern Python 3.11+ with type hints, async support, and clean architecture
- 📊 **Dual Analysis**: Combines fundamental metrics (P/E, earnings) with technical indicators (SMA, RSI, MACD)
- 🌐 **Triple Interface**: CLI tool, REST API, and interactive Web UI—all powered by single codebase

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.11+ | Core business logic and data processing |
| **REST API** | FastAPI | High-performance async API endpoints |
| **AI/LLM** | Ollama (Llama 3.2) | Local, privacy-preserving AI analysis |
| **Frontend** | HTML5/CSS3/JavaScript | Interactive Web dashboard |
| **Containers** | Docker & Docker Compose | Cloud-native deployment |
| **Data Source** | yfinance | Real-time market data |

### Analysis Capabilities

- **📊 Fundamental Analysis**: P/E ratios, earnings, balance sheets, income statements, analyst targets
- **📈 Technical Analysis**: Candlestick charts, SMA (20/50), RSI, MACD, Bollinger Bands, volume analysis
- **💼 Trading Strategy**: AI-generated entry/exit targets, stop loss, risk/reward ratios, timeframe recommendations
- **🤖 AI-Powered Insights**: LLM-generated recommendations, sentiment analysis, pattern recognition
- **🌐 REST API**: 25 production-ready endpoints with OpenAPI documentation
- **☁️ Cloud-Native**: Docker containerization for any cloud (AWS, Azure, GCP) or on-premises


## ⚡ Quick Start (2 Minutes)

### Using Docker (Recommended)
```bash
# 1. Start all services
docker compose up -d --build

# 2. Download AI model
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# 3. Access the platform
# 🌐 Web UI: http://localhost:8081
# 📚 API Docs: http://localhost:8000/docs
# ✅ Health Check: curl http://localhost:8000/health
```

### Local Development
```bash
# 1. Setup Python environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Start API server
python flow_api.py
# API runs on http://localhost:8000

# 3. Serve Web UI (separate terminal)
cd web && python -m http.server 8081
# Web UI on http://localhost:8081
```

**That's it!** Search for any stock ticker (e.g., AAPL, MSFT, TSLA) in the Web UI to see real-time analysis.

## 🎯 Key Features

### 1. Interactive Web Dashboard
- **Real-time stock search** with instant data loading
- **Professional candlestick charts** with hover tooltips
- **Technical indicators overlay**: SMA 20 (blue), SMA 50 (orange), Bollinger Bands (purple)
- **On-demand AI analysis** via buttons (no slow auto-loading)
- **Responsive design** optimized for desktop and tablet

### 2. Comprehensive REST API
- **24 production endpoints**: 13 data + 10 AI + 1 strategy + 2 health checks
- **Auto-generated documentation** with Swagger UI
- **CORS enabled** for web applications
- **Health monitoring** for app and AI services
- **Error handling** with meaningful HTTP status codes

### 3. AI-Powered Analysis & Trading Strategy
- **Fundamental analysis**: Company metrics, growth trends, financial health
- **Technical analysis**: Chart patterns, indicator interpretation, trend identification
- **Balance sheet analysis**: Asset quality, debt levels, liquidity
- **Income statement analysis**: Revenue trends, profitability, margins
- **News sentiment**: AI-powered sentiment from recent articles
- **Action recommendations**: Buy/sell/hold with detailed reasoning
- **Trading strategy**: Entry/exit targets, stop loss, risk/reward ratios, timeframe—all intelligently calculated from technical indicators and analyst targets

### 4. Intelligent Caching Layer
- **Market-aware SQLite caching** for all data and AI endpoints
- **Smart expiration logic** respecting US stock market hours (9:30 AM - 4:00 PM ET)
- **Cache management APIs** for stats, selective invalidation, and full flush
- **Performance optimization** reducing external API calls and LLM inference by up to 10x
- **Transparent operation** with automatic cache hit/miss handling—no configuration needed

### 5. Cloud-Native Architecture
- **Docker containerization** for consistent deployment
- **Multi-container orchestration** with Docker Compose
- **Service mesh** (Ollama + FastAPI + Nginx) with automatic health checks
- **Horizontal scalability** via stateless design
- **Environment parity** across dev, staging, production

### 6. Dual Analysis Approach

**Fundamental Analysis:**
- P/E ratio, market cap, EPS, dividend yield
- Balance sheet: assets, liabilities, equity
- Income statement: revenue, operating income, net income
- Analyst targets and consensus recommendations
- Earnings calendar and corporate events

**Technical Analysis:**
- 120+ days of OHLCV (candlestick) data
- Moving averages: SMA 20, SMA 50
- Volatility indicators: Bollinger Bands
- Momentum: RSI (14-period)
- Trend: MACD with signal line
- Volume analysis and patterns

### 7. Intelligent Trading Strategy Generation

**Automatically Generated Entry/Exit Strategy:**
- **Entry Targets**: Calculated from technical support levels and analyst targets
- **Exit Targets**: Three levels (conservative 5%, moderate 10%, aggressive 20%)
- **Stop Loss**: Determined from key technical support and SMA levels
- **Risk/Reward Ratio**: Calculated for position sizing and trade validation
- **Timeframe**: Intelligently suggested based on strategy confidence (1-6 months)
- **Confidence Levels**: HIGH/MEDIUM/LOW based on signal strength from multiple technical indicators
- **Integrated Analysis**: Combines RSI, MACD, Moving Averages, Bollinger Bands with analyst price targets

**Strategy Types:**
- **LONG**: Bullish setup with bullish technical signals (≥65% bullish indicators)
- **SHORT**: Bearish setup with bearish signals (≤35% bullish indicators)
- **WAIT**: Neutral/mixed signals with unclear direction (<35% or >65% threshold not met)

All strategies are displayed in the Web UI with color-coded cards (green for LONG, red for SHORT, gray for WAIT) and include supporting technical signals for validation.

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │  CLI Tool    │   REST API   │   Interactive Web UI     │ │
│  │  (flow.py)   │ (FastAPI)    │   (HTML5/CSS3/JS)        │ │
│  │              │ • 24 Endpoints│   • Candlestick Charts  │ │
│  │              │ • OpenAPI Docs│   • Real-time Search    │ │
│  │              │ • Health Checks│  • AI Analysis Buttons │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER (Python)                │
│  ┌─────────────────────────────┬───────────────────────────┐│
│  │   Data Processing           │   AI Analysis Engine      ││
│  │   • Fundamental metrics     │   • Technical patterns    ││
│  │   • Technical indicators    │   • Sentiment analysis    ││
│  │   • Price history           │   • LLM recommendations   ││
│  │   • News aggregation        │   • Context synthesis     ││
│  │   • Stock screening         │   • Report generation     ││
│  └─────────────────────────────┴───────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES & DATA SOURCES                │
│  ┌──────────────────────────────┬──────────────────────────┐│
│  │  Market Data (yfinance)      │  AI Engine (Ollama)      ││
│  │  • Real-time quotes          │  • Llama 3.2 model       ││
│  │  • Historical prices         │  • Local inference       ││
│  │  • Company fundamentals      │  • Privacy-preserving    ││
│  │  • News & analyst data       │  • Context-aware AI      ││
│  └──────────────────────────────┴──────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Container Architecture (Docker)

```
┌──────────────────────────────────────────────────────┐
│                  Docker Host                          │
│                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Nginx      │  │  FastAPI     │  │  Ollama    │ │
│  │   (Web)      │  │  (API)       │  │  (AI)      │ │
│  │              │  │              │  │            │ │
│  │ Port: 8081   │  │ Port: 8000   │  │Port: 11434 │ │
│  │              │  │              │  │            │ │
│  │ Serves:      │  │ Provides:    │  │ Runs:      │ │
│  │ • HTML/CSS/JS│  │ • REST API   │  │ • LLM      │ │
│  │ • Static     │  │ • OpenAPI    │  │ • Local AI │ │
│  │   Assets     │  │ • Health     │  │ • Inference│ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
│         ↓                  ↓                 ↓        │
│  ┌──────────────────────────────┐                   │
│  │    SQLite Cache Database     │                   │
│  │      (cache.db)              │                   │
│  │                              │                   │
│  │ Functions:                   │                   │
│  │ • API result caching         │                   │
│  │ • Market-aware expiration    │                   │
│  │ • Performance optimization   │                   │
│  └──────────────────────────────┘                   │
│         ↑                  ↑                 ↑        │
│  ┌──────────────────────────────────────────────┐   │
│  │        Docker Network (oobir_default)         │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘

### Caching Infrastructure (PostgreSQL)

OOBIR includes a robust caching layer backed by PostgreSQL to improve performance and reduce external API calls.

- **Cache Store**: `api_cache` table (JSONB payloads)
- **Expiry**: 24 hours by default
- **Keying**: `endpoint:symbol` plus additional parameters when present
- **Initialization**: Schema auto-created at app startup
- **Connection**: Managed via a pooled connection in `db.py`

Docker Compose provisions a `postgres` service and wires environment variables into the `app` service:

- `POSTGRES_HOST=postgres`
- `POSTGRES_PORT=5432`
- `POSTGRES_DB=oobir`
- `POSTGRES_USER=oobir`
- `POSTGRES_PASSWORD=oobir_password`

See `docker-compose.yml` for the full setup, including a persistent `postgres_data` volume and healthcheck.
```

### Caching Infrastructure

OOBIR includes a **sophisticated SQLite-based caching layer** (`db.py`) with **market-aware expiration logic** that intelligently balances performance with data freshness.

#### How It Works

The cache system respects US stock market hours (9:30 AM - 4:00 PM ET, Mon-Fri) to determine when data should be refreshed:

- **During Market Hours**: Cache expires if data was cached before today's 9:30 AM market open—ensuring fresh intraday data
- **After Market Close**: Cache remains valid through the night—avoiding unnecessary refetches during overnight analysis
- **Weekends/Holidays**: Cache valid for 24 hours (no market hours apply)
- **Absolute TTL**: All data expires after 24 hours regardless of market state

**Example Timeline:**
```
Monday 9:20 AM  → Cache price history
Monday 9:30 AM  → Market opens: cache expires (data is from before open)
Monday 11:00 AM → Fetch fresh data, cache it
Monday 2:00 PM  → Still cached (within market hours)
Monday 5:00 PM  → Market closed: cache still valid
Tuesday 9:20 AM → Cache still valid (< 24 hours old)
Tuesday 9:31 AM → Market opens: cache expires (old data from before open)
```

#### Cache Features

| Feature | Details |
|---------|---------|
| **Storage** | SQLite database (`cache.db`, auto-initialized) |
| **Endpoints** | All data endpoints leverage caching automatically |
| **Statistics** | Track hits, misses, and memory usage via API |
| **Control** | Per-symbol invalidation or full flush on demand |
| **Transparency** | No configuration needed—works automatically |

#### Cache Management API

```bash
# View cache statistics and performance metrics
curl http://localhost:8000/api/cache/stats

# Clear cache for specific symbol
curl -X DELETE http://localhost:8000/api/cache/AAPL

# Remove all expired entries
curl -X DELETE http://localhost:8000/api/cache/expired

# Flush entire cache
curl -X POST http://localhost:8000/api/cache-flush
```

**Sample Statistics Response:**
```json
{
  "total_entries": 45,
  "endpoints": {
    "price-history": 15,
    "fundamentals": 12,
    "news": 10,
    "ai-recommendation": 8
  },
  "by_symbol": {
    "AAPL": 8,
    "MSFT": 7,
    "TSLA": 5
  },
  "database_size_mb": 0.23,
  "oldest_entry_minutes": 12,
  "newest_entry_seconds": 3
}
```

#### Implementation Details

**Market-Aware Expiration Logic** (in `db.py`):
```python
def _should_expire_cache(cached_at_str: str) -> bool:
    # Always expire if older than 24 hours
    if (now - cached_at).total_seconds() > 86400:
        return True
    
    # During market hours: expire if before today's 9:30 AM open
    if _is_market_open_now():
        if cached_at < today_market_open:  # 9:30 AM
            return True
    else:
        # After market close: only expire if before today's open
        if now > today_market_close and cached_at < today_market_open:
            return True
    
    return False  # Cache is still valid
```

**FastAPI Integration** (in `flow_api.py`):
- All data endpoints automatically cache results using `with_cache()` wrapper
- AI analysis endpoints use `with_ai_cache()` with `market_aware=True` flag
- Cache hits return immediately; misses trigger fresh API calls

**Testing**: Comprehensive test suite in `tests/test_cache_layer.py` covers:
- CRUD operations (set, get, clear)
- Market-aware expiration with datetime mocking
- Complex data serialization (nested dicts, lists, empty data)
- Cache statistics and metrics

Run cache tests: `pytest tests/test_cache_layer.py -v`

### Technology Principles

1. **Single Codebase, Multiple Interfaces**: Business logic (`flow.py`) implemented once, exposed via CLI, REST API, and Web UI
2. **REST API First**: All functionality accessible via standardized HTTP endpoints
3. **AI Integration**: Ollama LLM seamlessly integrated for intelligent analysis
4. **Cloud-Native Design**: Stateless services support horizontal scaling
5. **Separation of Concerns**: Distinct layers for presentation, logic, and data
6. **Python-Powered**: Modern Python 3.11+ with type hints and async support

## Features

### 🎨 Interactive Web Dashboard
- **Real-Time Stock Search**: Search any ticker symbol with instant data loading
- **Enhanced Stock Header**: 
  - Company name with sector/industry display
  - Horizontal price trend summary (1D/1W/1M % change, 52W range, volume vs avg)
  - Clickable OOBIR logo for quick return to landing page
- **Company Summary Box**: Full business description with key details (website, employees, CEO, location)
- **Candlestick Chart with Technical Indicators**: Professional price history visualization with:
  - SMA 20 (blue line) - 20-period moving average
  - SMA 50 (orange line) - 50-period moving average
  - Bollinger Bands (purple shaded area) - 20-period with 2 standard deviations
  - Hover tooltips showing OHLC data
- **Smart Card Display**: Automatically hides empty data cards when no information available
- **Comprehensive Financial Data**: 
  - Fundamentals (P/E ratio, market cap, earnings, etc.)
  - Price history (120+ days of OHLCV data)
  - Balance sheet metrics
  - Income statement data
  - Analyst targets and consensus
  - Earnings calendar
- **On-Demand AI Analysis Buttons**: Click to run AI analysis (appears only when needed to avoid slow auto-loading):
  - AI Recommendation (buy/sell/hold with reasoning)
  - Technical Analysis (pattern recognition and indicator interpretation)
  - News & Sentiment Analysis (AI-powered sentiment from recent news)
- **Responsive Design**: Optimized for desktop and tablet viewing

### 🤖 Advanced AI & LLM Capabilities
- **LLM-Powered Intelligence**: Integrated Ollama LLM (huihui_ai/llama3.2-abliterate:3b) for sophisticated AI analysis
- **9 Specialized AI Analysis Functions**: Fundamental, technical, balance sheet, income statement, and full report generation
- **AI Technical Analysis**: LLM-powered analysis of technical indicators (precomputed SMA, RSI, MACD, Bollinger Bands, volume)
- **AI News Sentiment Analysis**: LLM-powered sentiment analysis of recent news articles for market context
- **Intelligent Recommendations**: AI-generated buy/sell/hold recommendations available in detailed, sentence, or single-word formats
- **Context-Aware Reasoning**: LLM synthesizes multiple data sources to provide nuanced, multi-perspective analysis


### 📊 Data Intelligence Layer
- **Multi-Source Financial Data**: Real-time and historical data across fundamentals, technicals, options, and analyst consensus
- **Earnings Intelligence**: Calendar events, quarterly financials, and historical trends
- **Market Sentiment**: Real-time news aggregation with AI-powered sentiment analysis
- **Stock Screening**: Algorithmic screening for undervalued large-cap stocks

### 🐳 Cloud & Container Deployment
- **Docker-First Architecture**: Containerized application with Docker Compose orchestration
- **Cloud-Native Ready**: Deploy to AWS, Azure, GCP, or on-premises with identical reproducibility
- **Service Mesh Integration**: Multi-container setup (app + web + Ollama) with automatic health checks
- **Environment Parity**: Guaranteed consistency across development, staging, and production
- **Scalability**: Stateless design supports horizontal scaling, load balancing, and orchestration (Kubernetes-compatible)

### 🚀 REST API & Platform Features
- **24 Comprehensive Endpoints**: 2 health checks, 13 data endpoints, 9 AI analysis endpoints
- **REST API with AutoDocs**: Full OpenAPI 3.0/Swagger documentation auto-generated by FastAPI
- **Triple Interface Architecture**: Identical functionality via CLI, REST API, and Web UI without code duplication
- **Health Monitoring**: Real-time service health checks for app and Ollama LLM with graceful fallbacks
- **Production Error Handling**: Comprehensive error responses with actionable messages and proper HTTP status codes
- **Enterprise Scalability**: Stateless design supports horizontal scaling via Docker and Kubernetes orchestration

## Installation

### From Source

```bash
git clone https://github.com/Greg-2600/oobir.git
cd oobir
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependencies

**Core Libraries:**
- FastAPI: REST API framework
- yfinance: Stock data fetching
- ollama: LLM integration
- requests: HTTP requests

**Frontend:**
- HTML5, CSS3, vanilla JavaScript (no external dependencies)

**Development:**
- pytest: Testing framework
- unittest.mock: Test mocking

See `requirements.txt` and `dev-requirements.txt` for full list.

## Web UI Usage

### Accessing the Web Dashboard

**With Docker (Recommended):**
```bash
docker compose up -d
# Open browser to http://localhost:8081
```

**Locally:**
```bash
# Terminal 1: Start API server
python flow_api.py
# Runs on http://localhost:8000

# Terminal 2: Serve web UI
cd web && python -m http.server 8081
# Open http://localhost:8081 in browser
```

**Remote Deployment:**
```bash
# After SSH to remote server
# Web UI: http://192.168.1.248:8081
# API Docs: http://192.168.1.248:8000/docs
```

### Using the Web Dashboard

1. **Search for a Stock**
   - Enter ticker symbol (e.g., AAPL, MSFT, TSLA)
   - Click search or press Enter
   - System auto-loads all financial data

2. **View Price History with Technical Indicators**
   - Featured candlestick chart displays at top
   - Green candles = price up, Red candles = price down
   - Blue line = SMA 20 (short-term trend)
   - Orange line = SMA 50 (long-term trend)
   - Purple shaded area = Bollinger Bands (volatility indicator)
   - Hover over candles to see exact OHLC values

3. **Review Financial Data**
   - Fundamentals: P/E ratio, market cap, earnings, ROE, etc.
   - Analyst Targets: Price targets and analyst recommendations
   - Balance Sheet: Assets, liabilities, equity
   - Income Statement: Revenue, earnings, margins
   - Calendar: Upcoming earnings dates and events

4. **Run AI Analysis (On-Demand)**
   - **AI Recommendation**: Click button to get buy/sell/hold recommendation with full reasoning
   - **Technical Analysis**: AI interpretation of technical indicators and price patterns
   - **News & Sentiment**: AI analysis of recent news and market sentiment
   - Results appear below each button after processing

### Web UI Files

```
web/
├── index.html      # Main HTML structure
├── styles.css      # Responsive styling
├── app.js          # Frontend logic and data visualization
└── config.js       # API base URL configuration
```

### Customizing the Web UI

**Change API Base URL:**
Edit `web/config.js`:
```javascript
const API_BASE_URL = 'http://192.168.1.248:8000'; // Change to your API server
```

**Styling:**
Edit `web/styles.css` to customize colors, fonts, layout, etc.

**Chart Colors:**
In `web/app.js`, modify the color constants in `renderPriceHistory()`:
- Green candles: `#22c55e`
- Red candles: `#ef4444`
- SMA 20: `#3b82f6`
- SMA 50: `#f59e0b`
- Bollinger Bands: `#a78bfa`


## CLI Usage

### Basic Data Retrieval

```bash
# Get fundamentals
python flow.py AAPL get_fundamentals

# Get price history
python flow.py MSFT get_price_history

# Get analyst targets
python flow.py TSLA get_analyst_price_targets

# List available functions
python flow.py --list
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

## REST API

### Starting the API Server

**Locally:**
```bash
python flow_api.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**With Docker:**
```bash
docker compose up -d
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### API Endpoints

**Health:**
- `GET /health` - Application health check
- `GET /health/ollama` - Ollama service health check

**Data Endpoints (13):**
- `GET /api/fundamentals/{symbol}` - Company fundamentals
- `GET /api/price-history/{symbol}` - Historical price data
- `GET /api/analyst-targets/{symbol}` - Analyst consensus
- `GET /api/calendar/{symbol}` - Earnings/events calendar
- `GET /api/income-stmt/{symbol}` - Quarterly income statement
- `GET /api/balance-sheet/{symbol}` - Balance sheet data
- `GET /api/option-chain/{symbol}` - Options data
- `GET /api/news/{symbol}` - Recent news articles
- `GET /api/screen-undervalued` - Stock screener

**AI Analysis Endpoints (10):**
> Preferred fast path: the UI "AI Recommendation" uses fundamental analysis for quicker responses.
- `GET /api/ai/fundamental-analysis/{symbol}` - AI fundamental analysis (preferred for speed)
- `GET /api/ai/balance-sheet-analysis/{symbol}` - AI balance sheet analysis
- `GET /api/ai/income-stmt-analysis/{symbol}` - AI income statement analysis
- `GET /api/ai/technical-analysis/{symbol}` - AI technical analysis
- `GET /api/ai/action-recommendation/{symbol}` - Detailed recommendation (slower; synthesizes multiple analyses)
- `GET /api/ai/action-recommendation-sentence/{symbol}` - One-sentence recommendation
- `GET /api/ai/action-recommendation-word/{symbol}` - Single word recommendation
- `GET /api/ai/news-sentiment/{symbol}` - AI sentiment analysis of news
- `GET /api/ai/full-report/{symbol}` - Comprehensive AI report

**Trading Strategy Endpoint:**
- `GET /api/trading-strategy/{symbol}` - AI-driven trading strategy with entry/exit targets, stop loss, risk/reward ratio, and timeframe

**Cache Management Endpoints:**
- `GET /api/cache/stats` — Aggregate cache statistics (total, valid, expired, by endpoint)
- `DELETE /api/cache/{symbol}` — Clear all cache entries for a symbol
- `DELETE /api/cache/expired` — Purge all expired cache entries

Caching applies to both data endpoints and AI endpoints. AI caching includes an Ollama availability check before inference; plain-string AI responses are cached safely.

### Example API Calls

```bash
# Get fundamentals
curl http://localhost:8000/api/fundamentals/AAPL

# Get AI fundamental analysis
curl http://localhost:8000/api/ai/fundamental-analysis/AAPL

# Get news sentiment
curl http://localhost:8000/api/ai/news-sentiment/CHTR

# Interactive API documentation
open http://localhost:8000/docs
```

## Docker Deployment

### Local Deployment

```bash
# Build and start
docker compose up -d --build

# Check logs
docker compose logs -f app

# Stop services
docker compose down
```

### Remote Deployment

Automated deployment script for remote servers:

```bash
./scripts/deploy_remote.sh <user@host> <remote_path>

# Example:
./scripts/deploy_remote.sh greg@192.168.1.248 ~/oobir
```

**Manual Steps:**
1. SSH to remote server
2. Clone repository
3. Run `docker compose up -d --build`
4. Pull model: `docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b`
5. Verify: `curl http://localhost:8000/health`

Notes:
- The deploy script forces rebuild (`up -d --build`) to ensure new code is included in the app image.
- If `docker compose` is unavailable, use `docker-compose` with the same flags.
- First-time model download can take time; the model is cached in the `ollama_data` volume.

**Undeploy Behavior:**
- The undeploy script preserves the Ollama model volume (`ollama_data`) so you don't re-download the model each time.
- SQLite cache file (`cache.db`) is preserved for future reference.
- To completely remove Ollama models, manually remove the `ollama_data` volume after undeploy.

### Undeploy

```bash
./scripts/undeploy_remote.sh
```

Removes containers, volumes, and cleans up resources while preserving the Ollama model.

## Available Functions

### Data Functions (9)

| Function | Description |
|----------|-------------|
| `get_fundamentals(ticker)` | Quarterly fundamentals (P/E, market cap, EPS, etc.) |
| `get_price_history(ticker)` | 121 days of historical OHLCV data |
| `get_analyst_price_targets(ticker)` | Analyst consensus and price targets |
| `get_calendar(ticker)` | Earnings dates and corporate events |
| `get_quarterly_income_stmt(ticker)` | Quarterly income statement |
| `get_balance_sheet(ticker)` | Balance sheet data |
| `get_option_chain(ticker)` | Options chain data (calls/puts) |
| `get_news(ticker)` | Recent news articles with summaries |
| `get_screen_undervalued_large_caps()` | Stock screener for undervalued stocks |

### AI Analysis Functions (10)

Requires Ollama with `huihui_ai/llama3.2-abliterate:3b` model installed.

| Function | Description |
|----------|-------------|
| `get_ai_fundamental_analysis(ticker)` | AI analysis of fundamental metrics |
| `get_ai_balance_sheet_analysis(ticker)` | AI insights on balance sheet health |
| `get_ai_quarterly_income_stm_analysis(ticker)` | AI analysis of income trends |
| `get_ai_technical_analysis(ticker)` | AI technical pattern recognition (uses precomputed SMA(20/50), RSI(14), MACD, Bollinger Bands, volume) |
| `get_ai_action_recommendation(ticker)` | Detailed buy/sell/hold recommendation |
| `get_ai_action_recommendation_sentence(ticker)` | One-sentence recommendation with reasoning |
| `get_ai_action_recommendation_single_word(ticker)` | Single word: BUY/SELL/HOLD |
| `get_ai_news_sentiment(ticker)` | AI sentiment analysis of top 5 recent news articles |
| `get_ai_full_report(ticker)` | Comprehensive multi-section AI report |
| `get_trading_strategy(ticker)` | AI-driven trading strategy with entry/exit targets, stop loss, risk/reward ratio, and timeframe |

## Architecture & Design

### System Architecture

```
┌───────────────────────────────────────────────────────────┐
│                 Presentation Layer                        │
├───────────────────────────────────────────────────────────┤
│   CLI Interface  │  REST API       │  Web UI              │
│   (flow.py)      │  (flow_api.py)  │  (HTML5/CSS3/JS)     │
│                  │  • 24 Endpoints │                      │
│                  │  • OpenAPI Docs │  • Real-time search  │
│                  │  • Health check │  • Charts & data     │
│                  │                 │  • AI analysis btn   │
├───────────────────────────────────────────────────────────┤
│          Business Logic Layer (flow.py - unified)         │
├───────────────────────────────────────────────────────────┤
│   Data Analysis           │   AI Analysis                  │
│   • Fundamentals          │   • LLM-powered insights       │
│   • Price history         │   • Technical pattern detect   │
│   • Balance sheets        │   • Sentiment analysis         │
│   • Income statements     │   • Recommendations            │
│   • Technical indicators  │   • Full report generation     │
├───────────────────────────────────────────────────────────┤
│      Intelligent Caching Layer (SQLite)                   │
├───────────────────────────────────────────────────────────┤
│   • API Response Cache (Market-aware expiration)          │
│   • Cache Statistics & Management APIs                    │
│   • 10x Performance improvement vs. uncached              │
├───────────────────────────────────────────────────────────┤
│        External Services & Data Sources                   │
├───────────────────────────────────────────────────────────┤
│   yfinance (Market Data)  │  Ollama LLM (Local AI)        │
│   • Stock fundamentals    │  • huihui_ai/llama3.2         │
│   • Historical prices     │  • Inference engine           │
│   • Options chains        │  • Context-aware analysis     │
│   • Analyst data          │  • Privacy-preserving         │
│   • News aggregation      │                               │
└───────────────────────────────────────────────────────────┘
```

### Frontend Architecture (Web UI)

```
┌─────────────────────────────────────────┐
│          Web UI (HTML5/CSS3/JS)          │
├─────────────────────────────────────────┤
│  Search Component   │   Data Display     │
│  • Ticker input     │   • Price chart    │
│  • Search button    │   • Fundamentals   │
│  • Quick search     │   • AI analysis    │
├─────────────────────────────────────────┤
│         Frontend Logic (app.js)          │
├─────────────────────────────────────────┤
│  • Fetch data from REST API              │
│  • Render candlestick chart              │
│  • Calculate technical indicators        │
│  • Handle user interactions              │
│  • On-demand AI button loading           │
├─────────────────────────────────────────┤
│    REST API (FastAPI) - 24 Endpoints     │
└─────────────────────────────────────────┘
```

### Architectural Principles

1. **Single Codebase, Multiple Interfaces**: Business logic implemented once, exposed via CLI, REST API, and Web UI—eliminates duplication and ensures consistency
2. **Separation of Concerns**: Distinct layers for presentation, business logic, and external integrations
3. **Frontend-Backend Separation**: Web UI communicates exclusively via REST API, allowing independent scaling and deployment
4. **Dependency Injection & Mocking**: Designed for testability with cleanly mockable external services
5. **Stateless Design**: Supports horizontal scaling and cloud deployment patterns
6. **Error Propagation**: Meaningful error messages bubble up from business logic through API layers
7. **Health-First Design**: Service health monitored at multiple levels with graceful degradation
8. **Technical Indicator Computation**: Client-side rendering with server-side data ensures optimal performance

### Technology Stack

**Core Infrastructure**
- **Language**: Python 3.11+ (modern, type-hint compatible)
- **Web Framework**: FastAPI (async-ready, auto-documented REST APIs)
- **Financial Data**: yfinance (open-source, free stock market data)
- **LLM Integration**: Ollama with huihui_ai/llama3.2-abliterate:3b (local, privacy-preserving)
- **Containerization**: Docker & Docker Compose (reproducible deployments)

**Testing & Quality**
- **Test Framework**: pytest (66 comprehensive tests)
- **Mocking**: unittest.mock (external dependency isolation)
- **Code Quality**: Type hints, docstrings, PEP 8 compliance

**Documentation**
- **API Docs**: OpenAPI 3.0 specification (auto-generated by FastAPI)
- **Interactive Docs**: Swagger UI + ReDoc (built into FastAPI)
- **Code Documentation**: Comprehensive docstrings and README

## Testing Strategy

### Comprehensive Test Coverage

OOBIR employs a rigorous testing strategy with **86 passing tests** achieving 100% endpoint coverage:

#### Test Architecture
- **Unit Tests**: Individual function testing with mocked external dependencies
- **Integration Tests**: End-to-end API endpoint testing with proper response validation
- **Web UI Integration**: Comprehensive testing of frontend-backend communication
- **Error Path Testing**: Verified error handling for invalid inputs and service failures
- **Dependency Mocking**: External services (Ollama, yfinance, SQLite cache) properly mocked to ensure test isolation and reliability
- **Database Cache Mocking**: All endpoints test both cache miss and cache write paths using `@patch('db.get_cached_data')` and `@patch('db.set_cached_data')`

#### Test Breakdown
| Category | Tests | Coverage |
|----------|-------|----------|
| Data Endpoints | 13 | All data retrieval functions |
| AI Analysis Endpoints | 38 | All AI analysis functions + news sentiment |
| Technical Indicators | 2 | Indicator calculations + AI prompt integration |
| Trading Strategy | 20 | Strategy generation, API endpoint, edge cases, integration |
| Web UI Integration | 13 | API format validation, CORS, error handling |
| **Total** | **86** | **100% of 25 API endpoints + Web UI + Strategy** |

#### Test Execution

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ai_analysis_endpoints.py -v

# Run tests in Docker
docker compose exec app pytest tests/ -v
```

#### Test Quality Metrics
- ✅ **25 API endpoints tested**: 13 data + 10 AI + 1 strategy + 2 health checks
- ✅ **100% endpoint coverage**: All REST endpoints fully tested
- ✅ **Web UI integration validated**: Frontend-backend communication verified
- ✅ **Success and error paths verified**: Both happy paths and error cases tested
- ✅ **Proper mocking of external dependencies**: Ollama, yfinance, SQLite cache properly mocked
- ✅ **Database caching behavior verified**: Cache hits/misses tested in all endpoints
- ✅ **Cache behavior verified**: Tests validate `set_cached_data()` is called exactly once per successful request

#### Test Files

**tests/test_data_endpoints.py** (13 tests)
- Fundamentals retrieval and validation
- Price history data accuracy
- Analyst targets and consensus data
- Calendar events and earnings dates
- Balance sheet and income statement data
- Options chain data
- News retrieval functionality
- Stock screening logic
- **All tests mock database caching**: `@patch('db.get_cached_data', return_value=None)` and `@patch('db.set_cached_data')`
- **Cache write verification**: Each test asserts `mock_set_cache.assert_called_once()`

**tests/test_ai_analysis_endpoints.py** (38 tests)
- Fundamental analysis accuracy
- Balance sheet analysis
- Technical analysis
- Income statement analysis
- Action recommendations (detailed, sentence, single-word)
- Full report generation
- **News Sentiment Analysis** (multi-test coverage for this novel feature)
- Error handling and fallback behavior
- **All AI tests mock database caching**: Cache mocks simulate cache misses and verify AI response caching

**tests/test_trading_strategy.py** (20 tests)
- **Unit Tests (10 tests)**: LONG strategy detection, SHORT strategy detection, WAIT strategy detection, insufficient data handling, None data handling, exception handling, technical levels calculation, analyst targets integration, exit target gain calculations, confidence level validation
- **API Endpoint Tests (6 tests)**: Basic endpoint functionality, cache hit verification, invalid ticker handling, API error handling, multi-symbol support
- **Integration Tests (3 tests)**: Signal consistency with strategy type, JSON serialization validation, comprehensive response structure validation
- **Edge Cases Covered**: Invalid tickers, insufficient price history (<20 days), missing analyst targets, exception handling, graceful WAIT strategy fallback
- **Technical Indicators Tested**: RSI, SMA (20/50), MACD, Bollinger Bands, Volume analysis
- **All trading strategy tests mock dependencies**: yfinance, analyst targets, database cache

### Run All Tests

```bash
# From virtual environment
source venv/bin/activate
pytest tests/ -v

# Using Docker
docker compose exec app pytest tests/ -v

# Run trading strategy tests specifically
pytest tests/test_trading_strategy.py -v
```

### Test Structure

- `tests/test_data_endpoints.py` - 13 tests for data endpoints
- `tests/test_ai_analysis_endpoints.py` - 38 tests for AI endpoints
- `tests/test_technical_indicators.py` - 2 tests for technical indicators
- `tests/test_trading_strategy.py` - 20 tests for trading strategy feature
- `tests/test_web_ui_integration.py` - 13 tests for Web UI integration
- `tests/scripts/` - Manual testing scripts and utilities

### Test Coverage

- ✅ **86 tests total** (13 data + 38 AI + 2 indicators + 20 trading + 13 Web UI)
- ✅ All 25 API endpoints tested
- ✅ Trading strategy generation fully tested (LONG, SHORT, WAIT scenarios + edge cases)
- ✅ Web UI integration validated
- ✅ Success and error paths verified
- ✅ Proper mocking of external dependencies (Ollama, yfinance, SQLite cache)
- ✅ Comprehensive edge case handling verified
- ✅ Database caching behavior verified in all endpoint tests
- ✅ Cache mocks return `None` to simulate cache misses and test full data flow
- ✅ Tests verify `set_cached_data()` is called exactly once per successful request

## Contributing

OOBIR is actively developed and welcomes contributions. Our development process emphasizes quality and testing:

### Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/your-feature`
2. **Implement with Tests**: Ensure new features include corresponding tests
3. **Verify Test Coverage**: Run full test suite: `pytest tests/ -v`
4. **Follow Code Standards**: PEP 8, type hints, docstrings
5. **Commit Clearly**: `git commit -m "Add feature description with context"`
6. **Push & Create PR**: `git push origin feature/your-feature` then create PR on GitHub
7. **CI/CD Review**: Verify all tests pass in PR checks

### Code Standards

- **Style Guide**: PEP 8 compliance
- **Type Hints**: All functions should include type annotations
- **Documentation**: Comprehensive docstrings following Google style
- **Testing**: Every feature must include tests; aim for >95% coverage
- **Error Handling**: Meaningful error messages and proper HTTP status codes

### Testing Requirements

```bash
# Before submitting PR, ensure:
pytest tests/ -v --tb=short     # All tests pass
pytest tests/ --cov=. --cov-report=term-missing  # Check coverage
```

### Pull Request Process

1. Update README.md with any new features or API changes
2. Include test results in PR description
3. Provide clear description of changes and motivation
4. Link any related issues
5. Maintain consistent formatting and code style

## Deployment

### Quick Deploy

```bash
./scripts/deploy_remote.sh <user@host> <path>
```

### Deployment Includes

- Docker container build
- Model download (huihui_ai/llama3.2-abliterate:3b)
- Health checks
- Service verification

### Production Considerations

- Use environment variables for configuration
- Set up monitoring and logging
- Configure backup strategy for model cache
- Use HTTPS for remote deployments
- Set resource limits in Docker Compose

## Testing

### Test Coverage

The project includes comprehensive test coverage across multiple layers:

- **Cache Layer Tests** (`tests/test_cache_layer.py`): 20+ tests for SQLite cache operations, market-aware expiration logic, statistics, and data serialization
- **API Endpoint Tests** (`tests/test_data_endpoints.py`): Tests for data API endpoints with mocked external services
- **AI Analysis Tests** (`tests/test_ai_analysis_endpoints.py`): Tests for AI analysis endpoints with Ollama LLM integration
- **Technical Indicator Tests** (`tests/test_technical_indicators.py`): Tests for technical indicator calculations
- **UI Tests** (`tests/ui/test_ui.py`): Selenium-based browser automation tests for frontend interactions

### Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_cache_layer.py -v
pytest tests/test_data_endpoints.py -v
pytest tests/test_ai_analysis_endpoints.py -v
```

Run tests with coverage report:
```bash
pytest tests/ --cov=. --cov-report=html
```

Run UI tests:
```bash
# Requires Selenium and Chrome/Firefox WebDriver
./scripts/test_ui.sh
```

### Testing the Cache Layer

The cache system includes dedicated tests for market-aware expiration:

```bash
# Run only cache tests
pytest tests/test_cache_layer.py::TestMarketAwareCaching -v

# This validates:
# - Cache expires at market open (9:30 AM ET)
# - Cache persists across market hours
# - 24-hour absolute TTL is respected
# - Non-market-aware endpoints have standard 1-hour TTL
```

### Cache Layer Test Classes

1. **TestCacheOperations**: Basic CRUD operations (set, get, clear)
2. **TestMarketAwareCaching**: Market-aware expiration logic with datetime mocking
3. **TestCacheStats**: Cache statistics and metrics reporting
4. **TestDataSerialization**: Complex nested data structure handling

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Verify model is downloaded
docker compose exec ollama ollama list

# Pull model if missing
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b
```

### API Port Already in Use

```bash
# Change port in docker-compose.yml or use different port
docker compose up -d -p 8001:8000
```

### Tests Failing

```bash
# Verify dependencies installed
pip install -r requirements.txt -r dev-requirements.txt

# Run tests with verbose output
pytest tests/ -vv --tb=short

# Run specific test file
pytest tests/test_data_endpoints.py -v
```

## License

See LICENSE file for details.

## Support & Contributing

For issues, questions, or contributions:
- **Issues & Bugs**: Please open an issue on GitHub with detailed reproduction steps
- **Feature Requests**: Describe the feature and expected behavior
- **Pull Requests**: Welcome! Please ensure tests pass and code follows project style

---

**Last Updated**: December 2025  
**Version**: 1.2.0  
**Status**: ✅ Production Ready  
**Features**: AI Analysis • Market-Aware Caching • Technical Indicators • REST API • Cloud-Native
