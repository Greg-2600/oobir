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
- 🔌 **REST API First**: 24 production-ready endpoints (13 data + 9 AI + 2 health) with auto-generated OpenAPI docs
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
- **🤖 AI-Powered Insights**: LLM-generated recommendations, sentiment analysis, pattern recognition
- **🌐 REST API**: 24 production-ready endpoints with OpenAPI documentation
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
- **24 production endpoints**: 13 data + 9 AI + 2 health checks
- **Auto-generated documentation** with Swagger UI
- **CORS enabled** for web applications
- **Health monitoring** for app and AI services
- **Error handling** with meaningful HTTP status codes

### 3. AI-Powered Analysis
- **Fundamental analysis**: Company metrics, growth trends, financial health
- **Technical analysis**: Chart patterns, indicator interpretation, trend identification
- **Balance sheet analysis**: Asset quality, debt levels, liquidity
- **Income statement analysis**: Revenue trends, profitability, margins
- **News sentiment**: AI-powered sentiment from recent articles
- **Action recommendations**: Buy/sell/hold with detailed reasoning

### 4. Database Caching Layer
- **PostgreSQL-backed caching** for all data and AI endpoints
- **24-hour cache expiration** with automatic cleanup
- **Cache management APIs** for stats, clearing, and monitoring
- **Performance optimization** reducing external API calls and LLM inference
- **Transparent caching** with automatic cache hit/miss handling

### 5. Cloud-Native Architecture
- **Docker containerization** for consistent deployment
- **Multi-container orchestration** with Docker Compose
- **Service mesh** (app + web + postgres + AI) with automatic health checks
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
│  ┌──────────────┐                                    │
│  │  PostgreSQL  │                                    │
│  │  (Database)  │                                    │
│  │              │                                    │
│  │ Port: 5432   │                                    │
│  │              │                                    │
│  │ Functions:   │                                    │
│  │ • API Cache  │                                    │
│  │ • Data Store │                                    │
│  │ • Persistent │                                    │
│  └──────────────┘                                    │
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

OOBIR includes a robust PostgreSQL-backed caching layer to improve performance and reduce external API calls.

**Cache Configuration:**
- **Storage**: `api_cache` table with JSONB payload support
- **Expiry**: 24 hours by default (configurable per endpoint)
- **Keys**: `endpoint:symbol` pattern with additional parameters
- **Initialization**: Schema auto-created at app startup
- **Connection**: Pooled connections managed via `db.py`

**Environment Variables:**
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=oobir
POSTGRES_USER=oobir
POSTGRES_PASSWORD=oobir_password
```

See `docker-compose.yml` for full configuration including persistent `postgres_data` volume.

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

**AI Analysis Endpoints (9):**
- `GET /api/ai/fundamental-analysis/{symbol}` - AI fundamental analysis
- `GET /api/ai/balance-sheet-analysis/{symbol}` - AI balance sheet analysis
- `GET /api/ai/income-stmt-analysis/{symbol}` - AI income statement analysis
- `GET /api/ai/technical-analysis/{symbol}` - AI technical analysis
- `GET /api/ai/action-recommendation/{symbol}` - Detailed recommendation
- `GET /api/ai/action-recommendation-sentence/{symbol}` - One-sentence recommendation
- `GET /api/ai/action-recommendation-word/{symbol}` - Single word recommendation
- `GET /api/ai/news-sentiment/{symbol}` - AI sentiment analysis of news
- `GET /api/ai/full-report/{symbol}` - Comprehensive AI report

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
- PostgreSQL cache volume (`postgres_data`) is removed to clear cached entries safely.
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

### AI Analysis Functions (9)

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
│          Caching & Persistence Layer (PostgreSQL)         │
├───────────────────────────────────────────────────────────┤
│   • API Response Cache (JSONB, 24-hour expiry)            │
│   • Cache Statistics & Management                         │
│   • Persistent Data Storage                               │
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

OOBIR employs a rigorous testing strategy with **66 passing tests** achieving 100% endpoint coverage:

#### Test Architecture
- **Unit Tests**: Individual function testing with mocked external dependencies
- **Integration Tests**: End-to-end API endpoint testing with proper response validation
- **Web UI Integration**: Comprehensive testing of frontend-backend communication
- **Error Path Testing**: Verified error handling for invalid inputs and service failures
- **Dependency Mocking**: External services (Ollama, yfinance, PostgreSQL) properly mocked to ensure test isolation and reliability
- **Database Cache Mocking**: All endpoints test both cache miss and cache write paths using `@patch('db.get_cached_data')` and `@patch('db.set_cached_data')`

#### Test Breakdown
| Category | Tests | Coverage |
|----------|-------|----------|
| Data Endpoints | 13 | All data retrieval functions |
| AI Analysis Endpoints | 38 | All AI analysis functions + news sentiment |
| Technical Indicators | 2 | Indicator calculations + AI prompt integration |
| Web UI Integration | 13 | API format validation, CORS, error handling |
| **Total** | **66** | **100% of 24 API endpoints + Web UI** |

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
- ✅ **100% Endpoint Coverage**: All 24 REST API endpoints tested
- ✅ **Success Path Validation**: Verified correct responses for valid inputs
- ✅ **Error Path Validation**: Tested error handling for edge cases and failures
- ✅ **External Dependency Isolation**: Ollama, yfinance, and PostgreSQL mocked to ensure tests run reliably without services
- ✅ **Cache Behavior Verification**: Every endpoint test verifies cache writes with `mock_set_cache.assert_called_once()`
- ✅ **Production-Ready**: Tests serve as executable documentation of expected behavior

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

### Run All Tests

```bash
# From virtual environment
source venv/bin/activate
pytest tests/ -v

# Using Docker
docker compose exec app pytest tests/ -v
```

### Test Structure

- `tests/test_data_endpoints.py` - 13 tests for data endpoints
- `tests/test_ai_analysis_endpoints.py` - 38 tests for AI endpoints
- `tests/test_technical_indicators.py` - 2 tests for technical indicators
- `tests/test_web_ui_integration.py` - 13 tests for Web UI integration
- `tests/scripts/` - Manual testing scripts and utilities

### Test Coverage

- ✅ **66 tests total** (13 data + 38 AI + 2 indicators + 13 Web UI)
- ✅ All 24 API endpoints tested
- ✅ Web UI integration validated
- ✅ Success and error paths verified
- ✅ Proper mocking of external dependencies (Ollama, yfinance, PostgreSQL)
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

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Last Updated**: January 2025  
**Version**: 1.2.0  
**Status**: Production Ready with Database Caching & Enhanced UI
