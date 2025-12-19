# OOBIR — Enterprise Stock Analysis & AI Recommendation Engine

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Supported-blue?logo=docker)
![Tests](https://img.shields.io/badge/Tests-53_Passing-brightgreen)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

## Overview

**OOBIR** is a sophisticated, production-grade **AI-driven stock analysis platform** that seamlessly integrates multi-source financial data with advanced **large language model (LLM) analysis**. Purpose-built for enterprise deployment with **cloud-native architecture** and containerized execution via Docker. This novel approach combines real-time market data, fundamental analysis, and AI-powered sentiment analysis to deliver actionable investment insights with institutional-grade reliability.

**Core Capabilities:**
- 🤖 **LLM-Powered Intelligence**: Ollama integration for local, privacy-preserving AI analysis
- 🐳 **Cloud-Ready Containerization**: Docker/Docker Compose for seamless multi-environment deployment
- 📊 **Intelligent Data Synthesis**: AI agents analyze multiple data sources simultaneously (fundamentals, technicals, sentiment)
- 🚀 **Scalable REST API**: 24 endpoints with auto-generated documentation and health monitoring

### Key Innovation

Unlike traditional stock analysis tools that separate data retrieval from analysis, OOBIR's unified architecture enables:
- **LLM-Native Architecture**: Purpose-built for AI-powered recommendations, not bolted-on. Full integration of Ollama LLM throughout analysis pipeline
- **Intelligent Data Synthesis**: AI agents analyze multiple data sources simultaneously (fundamentals, technicals, sentiment) with contextual reasoning
- **Context-Aware Recommendations**: LLM-powered analysis synthesizes news sentiment, balance sheet health, and technical patterns in single recommendations
- **Cloud-Native Deployment**: Containerized with Docker Compose—deploy locally, on-premises, or cloud (AWS/Azure/GCP) with identical reproducibility
- **Dual Interface**: Seamlessly operate via CLI or REST API without code duplication—single business logic, multiple access patterns
- **Production-Ready Testing**: Comprehensive 53-test suite with 100% endpoint coverage including mocked external dependencies

## Table of Contents

1. [Why OOBIR](#why-oobir)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Installation](#installation)
5. [CLI Usage](#cli-usage)
6. [REST API](#rest-api)
7. [Docker Deployment](#docker-deployment)
8. [Available Functions](#available-functions)
9. [Architecture & Design](#architecture--design)
10. [Testing Strategy](#testing-strategy)
11. [Contributing](#contributing)

## Why OOBIR?

### Novel Architectural Approach
- **Unified Data-Analysis Pipeline**: Unlike siloed tools, OOBIR's business logic layer serves both CLI and REST API without duplication, ensuring consistency across interfaces
- **LLM-Native Stock Analysis**: Purpose-built for AI-powered recommendations rather than bolting on LLM after-the-fact
- **Comprehensive Multi-Source Intelligence**: Synthesizes fundamentals, technicals, sentiment, and analyst consensus through AI reasoning

### Production Quality
- **53 Comprehensive Tests** covering all 24 API endpoints with success/failure paths and external dependency mocking
- **Health Monitoring**: Built-in health checks for application and Ollama LLM service with graceful degradation
- **Enterprise Error Handling**: Meaningful HTTP status codes and error messages for production systems
- **Cloud-Native Ready**: Single command deployment with Docker Compose—reproducible across development, staging, and production environments
- **AI Service Integration**: Seamless Ollama integration with automatic model management and health verification

## Quick Start

### Prerequisites
- Python 3.11+ (for local runs)
- Docker & Docker Compose (recommended for deployment)
- Ollama service (for AI analysis features)

### Local Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Docker Quick Start (Recommended)

```bash
# Start all services (app + ollama)
docker compose up -d --build

# Pull the AI model
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/health/ollama

# Access API documentation
open http://localhost:8000/docs
```

## Features

### 🤖 Advanced AI & LLM Capabilities
- **LLM-Powered Intelligence**: Integrated Ollama LLM (huihui_ai/llama3.2-abliterate:3b) for sophisticated AI analysis
- **9 Specialized AI Analysis Functions**: Fundamental, technical, balance sheet, income statement, and full report generation
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
- **Service Mesh Integration**: Multi-container setup (app + Ollama) with automatic health checks
- **Environment Parity**: Guaranteed consistency across development, staging, and production
- **Scalability**: Stateless design supports horizontal scaling, load balancing, and orchestration (Kubernetes-compatible)

### 🚀 REST API & Platform Features
- **24 Comprehensive Endpoints**: 2 health checks, 13 data endpoints, 9 AI analysis endpoints
- **REST API with AutoDocs**: Full OpenAPI 3.0/Swagger documentation auto-generated by FastAPI
- **Dual Interface Architecture**: Identical functionality via CLI (`flow.py`) or REST API (`flow_api.py`) without code duplication
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

**Development:**
- pytest: Testing framework
- unittest.mock: Test mocking

See `requirements.txt` and `dev-requirements.txt` for full list.

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
┌──────────────────────────────────────────────┐
│          Presentation Layer                  │
├──────────────────────────────────────────────┤
│   CLI Interface      │   REST API             │
│   (flow.py)          │   (flow_api.py)        │
│                      │   • 24 Endpoints       │
│                      │   • OpenAPI/Swagger    │
│                      │   • Health Checks      │
├──────────────────────────────────────────────┤
│      Business Logic Layer (Unified)          │
├──────────────────────────────────────────────┤
│   Data Functions     │   AI Analysis          │
│   • Fundamentals     │   • Technical Analysis │
│   • Technicals       │   • Sentiment Analysis │
│   • News             │   • Recommendations    │
│   • Screening        │   • Full Reports       │
├──────────────────────────────────────────────┤
│       External Services & Data Sources       │
├──────────────────────────────────────────────┤
│   yfinance (Market Data)  │  Ollama LLM       │
│   • Fundamentals          │  • Analysis       │
│   • Historical Prices     │  • Recommendations│
│   • Options Data          │  • Sentiment      │
│   • News Articles         │                   │
└──────────────────────────────────────────────┘
```

### Architectural Principles

1. **Single Codebase, Multiple Interfaces**: Business logic implemented once, exposed via CLI and REST API—eliminates duplication and ensures consistency
2. **Separation of Concerns**: Distinct layers for presentation, business logic, and external integrations
3. **Dependency Injection & Mocking**: Designed for testability with cleanly mockable external services
4. **Stateless Design**: Supports horizontal scaling and cloud deployment patterns
5. **Error Propagation**: Meaningful error messages bubble up from business logic through API layers
6. **Health-First Design**: Service health monitored at multiple levels with graceful degradation

### Technology Stack

**Core Infrastructure**
- **Language**: Python 3.11+ (modern, type-hint compatible)
- **Web Framework**: FastAPI (async-ready, auto-documented REST APIs)
- **Financial Data**: yfinance (open-source, free stock market data)
- **LLM Integration**: Ollama with huihui_ai/llama3.2-abliterate:3b (local, privacy-preserving)
- **Containerization**: Docker & Docker Compose (reproducible deployments)

**Testing & Quality**
- **Test Framework**: pytest (53 comprehensive tests)
- **Mocking**: unittest.mock (external dependency isolation)
- **Code Quality**: Type hints, docstrings, PEP 8 compliance

**Documentation**
- **API Docs**: OpenAPI 3.0 specification (auto-generated by FastAPI)
- **Interactive Docs**: Swagger UI + ReDoc (built into FastAPI)
- **Code Documentation**: Comprehensive docstrings and README

## Testing Strategy

### Comprehensive Test Coverage

OOBIR employs a rigorous testing strategy with **53 passing tests** achieving 100% endpoint coverage:

#### Test Architecture
- **Unit Tests**: Individual function testing with mocked external dependencies
- **Integration Tests**: End-to-end API endpoint testing with proper response validation
- **Error Path Testing**: Verified error handling for invalid inputs and service failures
- **Dependency Mocking**: External services (Ollama, yfinance) properly mocked to ensure test isolation and reliability

#### Test Breakdown
| Category | Tests | Coverage |
|----------|-------|----------|
| Data Endpoints | 13 | All data retrieval functions |
| AI Analysis Endpoints | 38 | All AI analysis functions + news sentiment |
| Technical Indicators | 2 | Indicator calculations + AI prompt integration |
| **Total** | **53** | **100% of 24 API endpoints** |

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
- ✅ **External Dependency Isolation**: Ollama and yfinance calls mocked to ensure tests run reliably without services
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

**tests/test_ai_analysis_endpoints.py** (38 tests)
- Fundamental analysis accuracy
- Balance sheet analysis
- Technical analysis
- Income statement analysis
- Action recommendations (detailed, sentence, single-word)
- Full report generation
- **News Sentiment Analysis** (multi-test coverage for this novel feature)
- Error handling and fallback behavior

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
- `tests/scripts/` - Manual testing scripts and utilities

### Test Coverage

- ✅ 53 tests total
- ✅ All 24 API endpoints tested
- ✅ Success and error paths verified
- ✅ Proper mocking of external dependencies (Ollama, yfinance)

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

**Last Updated**: December 18, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
