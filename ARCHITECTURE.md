# OOBIR System Architecture

Comprehensive documentation of OOBIR's system design, components, and data flow.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Module Descriptions](#module-descriptions)
5. [Key Design Decisions](#key-design-decisions)
6. [Technology Stack](#technology-stack)
7. [Deployment Architecture](#deployment-architecture)
8. [API Design Patterns](#api-design-patterns)

---

## System Overview

OOBIR is a multi-tier stock analysis application that combines real-time financial data with AI-powered insights. The system is designed to be modular, scalable, and deployable in multiple environments.

### Core Features

- **Data Layer**: Fetches real-time and historical stock data via yfinance
- **Analysis Layer**: Performs technical and fundamental analysis on stock data
- **AI Layer**: Generates AI-powered insights using Ollama LLMs
- **API Layer**: Exposes all functionality as a REST API via FastAPI
- **CLI Layer**: Provides command-line interface for direct access

### Architecture Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Loose Coupling**: Modules communicate through clear interfaces
3. **High Cohesion**: Related functionality grouped together
4. **Testability**: Easy to mock external dependencies
5. **Scalability**: Design supports horizontal and vertical scaling

---

## Component Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Client Layer                     │
├─────────────────────────────────────────────────────┤
│  CLI (flow.py)  │  REST API (flow_api.py)  │ Browser│
├─────────────────────────────────────────────────────┤
│                  Business Logic Layer                │
├─────────────────────────────────────────────────────┤
│  Data Functions (9)  │  Analysis  │  AI Analysis (8) │
├─────────────────────────────────────────────────────┤
│                    Integration Layer                 │
├─────────────────────────────────────────────────────┤
│  yfinance (Stock Data)  │  Ollama (LLM Inference)  │
├─────────────────────────────────────────────────────┤
│              External Services (Internet)            │
├─────────────────────────────────────────────────────┤
│  yfinance API  │  Ollama Server  │  Market Data APIs│
└─────────────────────────────────────────────────────┘
```

### Component Relationships

```
flow.py (Core Business Logic)
├── Data Fetching Functions
│   ├── get_fundamentals()
│   ├── get_price_history()
│   ├── get_analyst_price_targets()
│   ├── get_calendar()
│   ├── get_quarterly_income_stmt()
│   ├── get_balance_sheet()
│   ├── get_option_chain()
│   ├── get_news()
│   └── get_screen_undervalued_large_caps()
│
├── AI Analysis Functions
│   ├── get_ai_fundamental_analysis()
│   ├── get_ai_balance_sheet_analysis()
│   ├── get_ai_quarterly_income_stm_analysis()
│   ├── get_ai_technical_analysis()
│   ├── get_ai_action_recommendation()
│   ├── get_ai_action_recommendation_sentence()
│   ├── get_ai_action_recommendation_single_word()
│   └── get_ai_full_report()
│
└── Utility Functions
    ├── ensure_ollama()
    ├── list_available_functions()
    └── format_analysis()

flow_api.py (REST API Wrapper)
├── Health Check Endpoints (2)
├── Metadata Endpoints (4)
├── Data Endpoints (9) → calls flow.py functions
└── AI Endpoints (8) → calls flow.py functions
```

---

## Data Flow Diagrams

### Data Retrieval Flow

```
User Request (CLI or API)
        ↓
flow.py: get_fundamentals(ticker)
        ↓
yfinance.Ticker(ticker).info
        ↓
Parse & Format Response
        ↓
Return to User (dict or JSON)
```

### AI Analysis Flow

```
User Request (API/CLI)
        ↓
flow.py: get_ai_fundamental_analysis(ticker)
        ↓
Fetch fundamentals via get_fundamentals()
        ↓
Format data as analysis prompt
        ↓
Send to Ollama via ollama.chat()
        ↓
Ollama LLM processes request
        ↓
Parse LLM response
        ↓
Return analysis to User
```

### API Request/Response Flow

```
HTTP GET Request
        ↓
FastAPI Route Handler (flow_api.py)
        ↓
Call Corresponding flow.py Function
        ↓
Handle Exceptions
        ├─→ Success: Serialize Response → JSON 200 OK
        ├─→ AI Unavailable: Return 503 Service Unavailable
        └─→ Invalid Ticker: Return 500 with Error Details
        ↓
Return HTTP Response
```

### Docker Deployment Flow

```
Client (macOS)
        ↓
HTTP Request: localhost:8000
        ↓
Docker Host Network
        ↓
┌─────────────────────────────┐
│   Docker Compose Network    │
│                             │
│  ┌─────────────────────┐   │
│  │  app Container      │   │
│  │  - FastAPI Server   │   │
│  │  - flow.py logic    │   │
│  │  - Port: 8000       │   │
│  └────────┬────────────┘   │
│           │ (http://ollama:11434)
│  ┌────────▼────────────┐   │
│  │ ollama Container    │   │
│  │ - Ollama Server     │   │
│  │ - Port: 11434       │   │
│  │ - Model: llama3.2   │   │
│  └─────────────────────┘   │
│                             │
└─────────────────────────────┘
        ↓ (translated to localhost:11435)
        ↓
HTTP Response to Client
```

---

## Module Descriptions

### flow.py - Core Business Logic

**Purpose**: Implements all stock data fetching and analysis functions.

**Key Characteristics**:
- ~772 lines of Python code
- Single-responsibility functions (one function = one data source)
- Deferred Ollama import for flexible host configuration
- Comprehensive error handling
- Type hints throughout

**Main Functions**:

| Function | Purpose | Data Source |
|----------|---------|-------------|
| `get_fundamentals(ticker)` | Company fundamentals | yfinance |
| `get_price_history(ticker)` | Historical prices (121 days) | yfinance |
| `get_analyst_price_targets(ticker)` | Analyst recommendations | yfinance |
| `get_calendar(ticker)` | Earnings calendar | yfinance |
| `get_quarterly_income_stmt(ticker)` | Income statement | yfinance |
| `get_balance_sheet(ticker)` | Balance sheet | yfinance |
| `get_option_chain(ticker)` | Options data | yfinance |
| `get_news(ticker)` | Latest news | yfinance |
| `get_screen_undervalued_large_caps()` | Stock screener | yfinance |

**AI Functions** (8 total):
- All use the `huihui_ai/llama3.2-abliterate:3b` model
- Generate contextual prompts from financial data
- Return structured text analysis

**Key Utilities**:
- `ensure_ollama(host)`: Configures and validates Ollama connection
- `list_available_functions()`: Returns callable function metadata
- Prompt generation functions for AI analysis

### flow_api.py - REST API Layer

**Purpose**: Exposes flow.py functions as a REST API with 23 endpoints.

**Key Characteristics**:
- ~427 lines of code
- FastAPI framework for automatic OpenAPI documentation
- Custom JSON serialization for pandas/numpy types
- Comprehensive error handling (503 for AI failures, 500 for data errors)
- Health check endpoints for monitoring
- Request logging with timestamps

**Endpoint Categories**:

1. **Metadata Endpoints (4)**:
   - `GET /` - API info and current configuration
   - `GET /docs` - Interactive Swagger UI
   - `GET /redoc` - ReDoc documentation
   - `GET /openapi.json` - OpenAPI schema

2. **Health Endpoints (2)**:
   - `GET /health` - General health check
   - `GET /health/ollama` - Ollama connectivity check

3. **Data Endpoints (9)**:
   - Direct mappings to flow.py data functions
   - Path parameters for ticker symbols
   - Returns 500 with error details on failure

4. **AI Endpoints (8)**:
   - Direct mappings to flow.py AI functions
   - Returns 503 if Ollama unavailable
   - Returns 500 for other errors

**JSON Serialization**:
```python
def serialize_value(obj):
    """Handles pandas, numpy, datetime, NaN, Infinity."""
    # Custom logic for complex types
```

### docker-compose.yml - Container Orchestration

**Services**:

1. **app** (FastAPI Application)
   - Image: Built from Dockerfile
   - Port: 8000 (HTTP)
   - Environment: OLLAMA_HOST, PYTHONUNBUFFERED
   - Dependencies: Ollama service
   - Entrypoint: FastAPI server

2. **ollama** (LLM Server)
   - Image: `ollama/ollama:latest`
   - Port: 11434 (internal) / 11435 (host)
   - Volume: ollama_data (persistent)
   - Purpose: LLM inference engine

**Network**: Both services on shared Docker network for internal communication.

### Dockerfile - Container Image

**Base Image**: `python:3.11-slim` (optimized for size)

**Build Process**:
1. Create working directory: `/home/app/oobir`
2. Copy requirements.txt
3. Install system dependencies (libssl-dev, etc.)
4. Install Python packages
5. Copy application code
6. Set environment variables
7. Expose port 8000
8. Run FastAPI server on startup

**Optimizations**:
- Slim base image (reduces size)
- Multi-stage builds not used (simple requirements)
- Dependency layer caching

### tests/ - Test Suite

**Test Structure**:
```
tests/
├── test_flow.py           # Unit tests for flow.py (7 tests)
├── test_flow_api.py       # Integration tests for flow_api.py (16 tests)
└── (manual) see root-level shell scripts for live endpoint tests:
        - test_data_endpoints.sh  # Data endpoint smoke tests
        - test_ai_endpoints.sh    # AI endpoint smoke tests
```

**Testing Strategy**:
- **Mocking**: Mock yfinance and ollama to avoid network calls
- **Fixtures**: Reusable test data and mock responses
- **Parametrization**: Test multiple scenarios with same test
- **Integration**: Verify components work together

**Coverage**: ~85% code coverage across all modules

---

## Key Design Decisions

### 1. Deferred Ollama Import

**Decision**: Import Ollama client at runtime, not module load time.

**Rationale**:
- Allows `--host` flag to override host before connection
- Enables environment variable configuration
- Supports both local and remote Ollama instances
- Prevents import failures on systems without Ollama installed

**Implementation**:
```python
_CHAT = None

def ensure_ollama(host=None):
    global _CHAT
    if _CHAT is None:
        from ollama import chat
        _CHAT = chat
```

### 2. Mock Testing Architecture

**Decision**: Mock external services (yfinance, Ollama) in tests.

**Rationale**:
- Tests run without network access
- Consistent, reproducible results
- Fast test execution (~< 1 second)
- Can test error conditions easily
- No API rate limiting issues

### 3. Graceful Degradation

**Decision**: AI endpoints return 503 when Ollama unavailable, not 200 with null.

**Rationale**:
- Clear error indication (not a success response with no data)
- Enables client-side retry logic with backoff
- Supports health monitoring and alerting
- Different HTTP semantics for different failure modes

**Error Codes**:
- 200: Success
- 500: Data error (yfinance failed)
- 503: Service unavailable (Ollama failed)

### 4. Automatic JSON Serialization

**Decision**: Custom serializer for pandas/numpy types in responses.

**Rationale**:
- yfinance returns pandas DataFrames with numpy dtypes
- JSON doesn't natively support these types
- Custom serialization handles NaN, Infinity properly
- FastAPI can't serialize these automatically

### 5. Single Ollama Model

**Decision**: Use single `huihui_ai/llama3.2-abliterate:3b` model for all AI tasks.

**Rationale**:
- Reduces model switching overhead
- Smaller 3B model fits on CPU and modest GPU
- Good balance of speed and quality
- Simplifies deployment and maintenance

### 6. Health Check Endpoints

**Decision**: Implement `/health` and `/health/ollama` endpoints.

**Rationale**:
- Enable external monitoring (Kubernetes liveness probes)
- Detect Ollama failures without making full requests
- Support alerting on service degradation
- Quick diagnostics for operators

### 7. RESTful API Design

**Decision**: Pure GET endpoints, no POST/PUT/DELETE.

**Rationale**:
- Read-only operations (no state changes)
- Simplifies caching and CDN compatibility
- Easier to reason about side effects
- Suitable for financial data (no write operations needed)

---

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Programming language |
| FastAPI | 0.104.0+ | REST API framework |
| Uvicorn | 0.24.0+ | ASGI server |
| yfinance | Latest | Stock market data |
| pandas | Latest | Data manipulation |
| numpy | Latest | Numerical computing |
| Ollama | Latest | LLM inference |

### Testing

| Technology | Purpose |
|------------|---------|
| pytest | Test framework |
| unittest.mock | Mocking library |
| pytest-cov | Coverage reporting |

### Deployment

| Technology | Purpose |
|-----------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| Dockerfile | Container image definition |

### Development

| Technology | Purpose |
|-----------|---------|
| Git | Version control |
| Ruff | Linting and formatting |
| pylint | Code analysis |
| Black | Code formatter |

---

## Deployment Architecture

### Local Development

```
Developer Machine (macOS)
├── Python venv
├── flow.py (CLI)
├── flow_api.py (API server)
└── Ollama (Docker container)
```

### Docker Compose (Recommended)

```
Host Machine
└── Docker Engine
    ├── app Container (FastAPI, Python 3.11)
    │   ├── flow.py
    │   ├── flow_api.py
    │   └── Dependencies (yfinance, pandas, numpy)
    │
    └── ollama Container (LLM Server)
        ├── Ollama Service
        ├── Model: llama3.2-abliterate:3b
        └── Persistent Volume: ollama_data
```

### Remote Deployment

```
Local Machine (macOS)
    │
    └─→ SSH/SCP
        │
        └─→ Remote Linux Server (192.168.1.248)
            └── Docker Engine
                ├── app Container
                └── ollama Container
                    │
                └─→ Accessible at http://192.168.1.248:8000
```

---

## API Design Patterns

### Request/Response Pattern

**Pattern**: Uniform REST API with predictable URL structure.

```
GET /api/{resource}/{identifier}
GET /api/ai/{analysis_type}/{identifier}
```

**Example**:
```bash
# Data endpoint
GET /api/fundamentals/AAPL → Returns fundamentals JSON

# AI endpoint  
GET /api/ai/action-recommendation/AAPL → Returns AI recommendation JSON
```

### Error Handling Pattern

**Pattern**: Consistent error responses with HTTP status codes.

```python
# Data endpoint error
{
    "detail": "yfinance failed: Invalid ticker INVALID_TICKER"
}
# HTTP 500

# AI endpoint error (Ollama down)
{
    "detail": "AI service unavailable: Ollama not responding"
}
# HTTP 503
```

### Health Check Pattern

**Pattern**: Dedicated health endpoints for monitoring.

```bash
# General health
GET /health → {"status": "healthy"}

# Dependency health
GET /health/ollama → {"status": "healthy"}
```

### Metadata Pattern

**Pattern**: Expose API metadata and documentation.

```bash
GET /           → {"name": "OOBIR", "version": "1.0", ...}
GET /docs       → Interactive Swagger UI
GET /redoc      → ReDoc documentation
GET /openapi.json → OpenAPI schema
```

### Serialization Pattern

**Pattern**: Custom JSON encoder handles complex types.

```python
# Pandas types
DataFrame → Serialized to JSON

# NumPy types
np.float64(3.14) → 3.14

# Special values
np.nan → null
np.inf → "Infinity"

# Dates
datetime.date(2025, 1, 1) → "2025-01-01"
```

---

## Performance Considerations

### Response Time

| Endpoint | Time | Notes |
|----------|------|-------|
| Data endpoints | ~500ms-2s | Depends on yfinance API |
| AI endpoints | ~30-60s | CPU-intensive LLM inference |
| Health checks | ~10-100ms | Quick status checks |

### Optimization Strategies

1. **Caching**: Cache yfinance responses for frequently requested tickers
2. **Async Processing**: Consider async yfinance fetching for batch requests
3. **GPU Acceleration**: Ollama can use GPU for faster AI inference
4. **Connection Pooling**: Reuse HTTP connections to yfinance

### Resource Requirements

| Resource | Requirement | Notes |
|----------|-------------|-------|
| CPU | 2+ cores | Ollama is CPU-bound |
| RAM | 4GB+ | For 3B parameter model |
| Disk | 5GB+ | For Ollama model storage |
| Network | 10Mbps+ | For yfinance API calls |

---

## Scalability Considerations

### Horizontal Scaling

To scale multiple API instances:

1. **Load Balancer**: Nginx/HAProxy in front of multiple app instances
2. **Shared Ollama**: Single Ollama instance shared by multiple app instances
3. **Database**: Optional: Caching layer (Redis) for frequent requests

### Vertical Scaling

To improve single-instance performance:

1. **GPU**: Enable GPU acceleration for Ollama
2. **Larger Model**: Use larger Ollama model (7B, 13B)
3. **Async Processing**: Implement async yfinance fetching
4. **Connection Pooling**: Optimize network connections

---

## Security Architecture

### Current State

⚠️ **No Authentication**: This system has no authentication or authorization.

### Recommended for Production

1. **API Gateway**: Implement API gateway with authentication
2. **TLS/HTTPS**: Use HTTPS for all communications
3. **Rate Limiting**: Limit requests per client
4. **API Keys**: Implement API key authentication
5. **CORS**: Restrict cross-origin requests
6. **Input Validation**: Validate all user inputs
7. **Network Isolation**: Run in private network with firewall

---

## Monitoring and Observability

### Logging

**Current Implementation**:
- INFO-level logging with timestamps
- Logs to stdout (captured by Docker)
- Includes function name, level, and message

**Accessible via**:
```bash
docker compose logs -f app
docker compose logs -f ollama
```

### Health Checks

**Available Endpoints**:
- `/health` - General health
- `/health/ollama` - Ollama connectivity

### Future Enhancements

1. **Metrics**: Prometheus metrics on response times, error rates
2. **Distributed Tracing**: Jaeger for request tracing
3. **Log Aggregation**: ELK stack or Datadog
4. **Alerting**: PagerDuty/Slack notifications

---

## Summary

OOBIR's architecture emphasizes:

- **Modularity**: Clear separation of concerns
- **Testability**: Easy to mock and test
- **Reliability**: Graceful error handling
- **Observability**: Health checks and logging
- **Extensibility**: Easy to add new functions and endpoints
- **Deployability**: Docker support for consistent environments

This design enables OOBIR to be both developer-friendly and production-ready while remaining simple and maintainable.

---

**Last Updated**: December 17, 2025
