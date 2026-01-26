"""FastAPI application exposing flow.py functions as REST endpoints.

No authentication; suitable for internal networks only.
"""

import os
import json
import logging
from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import flow
import db  # Database caching layer

# Helper to convert non-JSON-serializable objects to strings
def serialize_value(obj):  # pylint: disable=too-many-return-statements
    """Recursively convert non-JSON-serializable objects to strings."""
    if isinstance(obj, dict):
        return {str(k): serialize_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize_value(item) for item in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, (float, np.floating)):
        # Handle NaN and Infinity
        if pd.isna(obj):
            return None
        if np.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        return float(obj)  # Convert numpy floats to Python float
    if isinstance(obj, (int, np.integer)):
        return int(obj)  # Convert numpy ints to Python int
    if hasattr(obj, 'isoformat'):  # pandas Timestamp, datetime-like
        return obj.isoformat()
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    return obj

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OOBIR Stock Analysis API",
    description="REST API for stock analysis and AI recommendations",
    version="1.0.0"
)

# CORS for web UI (allow local and LAN UI origins)
allowed_origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://192.168.1.248",
    "http://192.168.1.248:8080",
    "http://192.168.1.248:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins + ["*"],  # permissive during development
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"]
)

# Set Ollama host from environment or use default
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
logger.info("Ollama host configured: %s", OLLAMA_HOST)

# Initialize database connection pool on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("OOBIR Stock Analysis API starting up")


# System/Cache Endpoints
@app.get("/api/health")
def health_endpoint():
    """Health check endpoint."""
    return {"status": "ok", "service": "OOBIR Stock Analysis API"}


@app.get("/api/cache-info")
def cache_info():
    """Get cache information."""
    return db.get_cache_stats()


@app.post("/api/cache-flush")
def flush_cache(endpoint: str = None, symbol: str = None):
    """
    Clear cache entries.
    
    Query Parameters:
        endpoint: Optional endpoint name to clear (e.g., 'price-history')
        symbol: Optional stock symbol to clear (e.g., 'AAPL')
    
    If both are omitted, entire cache is cleared.
    """
    count = db.clear_cache(endpoint=endpoint, symbol=symbol)
    return {"cleared": count, "message": f"Cleared {count} cache entries"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Starting OOBIR API...")
    logger.info("Database cache initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down OOBIR API...")
    # Connection pool cleanup handled automatically


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "OOBIR Stock Analysis API",
        "docs": "/docs",
        "redoc": "/redoc",
        "ollama_host": OLLAMA_HOST
    }


@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "oobir-api",
        "ollama_configured": OLLAMA_HOST
    }


@app.get("/health/ollama")
def health_check_ollama():
    """Health check endpoint that tests Ollama connectivity."""
    logger.info("Ollama health check requested")
    try:
        import requests  # pylint: disable=import-outside-toplevel
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama health check: OK")
            return {
                "status": "healthy",
                "ollama_host": OLLAMA_HOST,
                "ollama_reachable": True,
                "ollama_response_code": 200
            }
        logger.warning("Ollama returned non-200: %s", response.status_code)
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "ollama_host": OLLAMA_HOST,
                "ollama_reachable": True,
                "ollama_response_code": response.status_code,
                "error": "Ollama returned unexpected status code"
            }
        )
    except requests.exceptions.Timeout:  # pylint: disable=broad-except
        logger.error("Ollama health check timeout: %s", OLLAMA_HOST)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "ollama_host": OLLAMA_HOST,
                "ollama_reachable": False,
                "error": "Timeout connecting to Ollama"
            }
        )
    except requests.exceptions.ConnectionError as exc:
        logger.error("Ollama health check connection error: %s", str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "ollama_host": OLLAMA_HOST,
                "ollama_reachable": False,
                "error": f"Cannot connect to Ollama: {str(exc)}"
            }
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Ollama health check failed: %s", str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "ollama_host": OLLAMA_HOST,
                "error": str(exc)
            }
        )


def with_cache(endpoint: str, symbol: str, flow_function, *args, **kwargs):
    """
    Wrapper to check cache before calling flow function.
    
    Args:
        endpoint: Endpoint name for cache key
        symbol: Stock ticker symbol
        flow_function: Function from flow.py to call if cache miss
        *args, **kwargs: Arguments to pass to flow_function
        
    Returns:
        Cached data or fresh data from flow_function
    """
    # Try to get from cache first
    cached_data = db.get_cached_data(endpoint, symbol)
    if cached_data is not None:
        logger.info(f"Returning cached data for {endpoint}/{symbol}")
        return cached_data
    
    # Cache miss - call the actual function
    logger.info(f"Cache miss for {endpoint}/{symbol}, fetching fresh data")
    result = flow_function(symbol, *args, **kwargs)
    
    # Parse JSON string if needed
    if isinstance(result, str):
        result = json.loads(result)
    
    # Serialize and cache the result
    serialized_result = serialize_value(result)
    db.set_cached_data(endpoint, serialized_result, symbol)
    
    return serialized_result


def with_ai_cache(endpoint: str, symbol: str, flow_function, *args, **kwargs):
    """Wrapper to cache AI responses while ensuring Ollama is available."""
    cached_data = db.get_cached_data(endpoint, symbol)
    if cached_data is not None:
        logger.info("Returning cached AI data for %s/%s", endpoint, symbol)
        return cached_data

    logger.info("Cache miss for %s/%s, calling AI model", endpoint, symbol)
    
    # Ensure Ollama is reachable before invoking
    flow.ensure_ollama(OLLAMA_HOST)

    result = flow_function(symbol, *args, **kwargs)
    if result is None:
        logger.error("AI endpoint %s returned None for %s", endpoint, symbol)
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable - Ollama connection failed or returned no response"
        ) from None
    
    # AI functions return plain strings, not JSON strings
    # Only attempt JSON parsing if it looks like JSON (starts with { or [)
    if isinstance(result, str) and result.strip().startswith(('{', '[')):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            # If JSON parsing fails, keep as plain string
            pass

    serialized_result = serialize_value(result)
    logger.info("Caching AI response for %s/%s", endpoint, symbol)
    db.set_cached_data(endpoint, serialized_result, symbol, market_aware=True)
    return serialized_result


# ============================================================================
# Data Endpoints
# ============================================================================

@app.get("/api/fundamentals/{symbol}")
def get_fundamentals(symbol: str):
    """Get fundamentals for a given stock symbol."""
    logger.info("Fetching fundamentals for %s", symbol)
    try:
        result = with_cache("fundamentals", symbol, flow.get_fundamentals)
        # get_fundamentals returns a JSON string, so parse it first
        if isinstance(result, str):
            result = json.loads(result)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching fundamentals for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/price-history/{symbol}")
def get_price_history(symbol: str):
    """Get historical price data for a given stock symbol."""
    logger.info("Fetching price history for %s", symbol)
    try:
        result = with_cache("price-history", symbol, flow.get_price_history)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching price history for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/analyst-targets/{symbol}")
def get_analyst_targets(symbol: str):
    """Get analyst price targets for a given stock symbol."""
    logger.info("Fetching analyst targets for %s", symbol)
    try:
        result = with_cache("analyst-targets", symbol, flow.get_analyst_price_targets)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching analyst targets for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/calendar/{symbol}")
def get_calendar(symbol: str):
    """Get earnings calendar for a given stock symbol."""
    logger.info("Fetching calendar for %s", symbol)
    try:
        result = with_cache("calendar", symbol, flow.get_calendar)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching calendar for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/balance-sheet/{symbol}")
def get_balance_sheet(symbol: str):
    """Get balance sheet data for a given stock symbol."""
    logger.info("Fetching balance sheet for %s", symbol)
    try:
        result = with_cache("balance-sheet", symbol, flow.get_balance_sheet)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching balance sheet for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/income-stmt/{symbol}")
def get_income_stmt(symbol: str):
    """Get quarterly income statement for a given stock symbol."""
    logger.info("Fetching income statement for %s", symbol)
    try:
        result = with_cache("income-stmt", symbol, flow.get_quarterly_income_stmt)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching income statement for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/news/{symbol}")
def get_news(symbol: str):
    """Get news for a given stock symbol."""
    logger.info("Fetching news for %s", symbol)
    try:
        result = with_cache("news", symbol, flow.get_news)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching news for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/option-chain/{symbol}")
def get_option_chain(symbol: str):
    """Get option chain for a stock."""
    logger.info("Fetching option chain for %s", symbol)
    try:
        result = with_cache("option-chain", symbol, flow.get_option_chain)
        result = serialize_value(result)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching option chain for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/screen-undervalued")
def get_screen_undervalued_large_caps():
    """Get screen of undervalued large cap stocks."""
    logger.info("Fetching undervalued large caps screen")
    try:
        # Check cache first
        cached_data = db.get_cached_data("screen-undervalued", "ALL")
        if cached_data is not None:
            logger.info("Returning cached data for screen-undervalued")
            return JSONResponse(content=cached_data)
        
        # Cache miss - fetch fresh data
        logger.info("Cache miss for screen-undervalued, fetching fresh data")
        result = flow.get_screen_undervalued_large_caps()
        
        # Cache the result
        db.set_cached_data("screen-undervalued", result, "ALL")
        
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching undervalued screen: %s", str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ============================================================================
# Cache Management Endpoints
# ============================================================================

@app.get("/api/cache/stats")
def get_cache_stats():
    """Get cache statistics."""
    logger.info("Cache stats requested")
    try:
        stats = db.get_cache_stats()
        return JSONResponse(content=stats)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error getting cache stats: %s", str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/api/cache/{symbol}")
def clear_symbol_cache(symbol: str):
    """Clear cache for a specific symbol."""
    logger.info("Clearing cache for %s", symbol)
    try:
        deleted_count = db.clear_symbol_cache(symbol)
        return JSONResponse(content={
            "symbol": symbol,
            "deleted_entries": deleted_count,
            "message": f"Cleared {deleted_count} cache entries for {symbol}"
        })
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error clearing cache for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/api/cache/expired")
def clear_expired_cache():
    """Clear all expired cache entries."""
    logger.info("Clearing expired cache entries")
    try:
        deleted_count = db.clear_expired_cache()
        return JSONResponse(content={
            "deleted_entries": deleted_count,
            "message": f"Cleared {deleted_count} expired cache entries"
        })
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error clearing expired cache: %s", str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ============================================================================
# AI Analysis Endpoints (requires Ollama)
# ============================================================================

@app.get("/api/ai/fundamental-analysis/{symbol}")
def get_ai_fundamental_analysis(symbol: str):
    """Get AI analysis of fundamentals for a stock."""
    logger.info("AI fundamental analysis requested for %s", symbol)
    try:
        result = with_ai_cache("ai-fundamental-analysis", symbol, flow.get_ai_fundamental_analysis)
        logger.info("Successfully generated AI fundamental analysis for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI fundamental analysis for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/balance-sheet-analysis/{symbol}")
def get_ai_balance_sheet_analysis(symbol: str):
    """Get AI analysis of balance sheet for a stock."""
    logger.info("AI balance sheet analysis requested for %s", symbol)
    try:
        result = with_ai_cache("ai-balance-sheet-analysis", symbol, flow.get_ai_balance_sheet_analysis)
        logger.info("Successfully generated AI balance sheet analysis for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI balance sheet analysis for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/income-stmt-analysis/{symbol}")
def get_ai_quarterly_income_stm_analysis(symbol: str):
    """Get AI analysis of income statement for a stock."""
    logger.info("AI income statement analysis requested for %s", symbol)
    try:
        result = with_ai_cache("ai-income-stmt-analysis", symbol, flow.get_ai_quarterly_income_stm_analysis)
        logger.info("Successfully generated AI income statement analysis for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI income statement analysis for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/technical-analysis/{symbol}")
def get_ai_technical_analysis(symbol: str):
    """Get AI technical analysis for a stock."""
    logger.info("AI technical analysis requested for %s", symbol)
    try:
        result = with_ai_cache("ai-technical-analysis", symbol, flow.get_ai_technical_analysis)
        logger.info("Successfully generated AI technical analysis for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI technical analysis for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/action-recommendation/{symbol}")
def get_ai_action_recommendation(symbol: str):
    """Get AI action recommendation (buy/sell/hold) for a stock."""
    logger.info("AI action recommendation requested for %s", symbol)
    try:
        result = with_ai_cache("ai-action-recommendation", symbol, flow.get_ai_action_recommendation)
        logger.info("Successfully generated AI action recommendation for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI action recommendation for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/action-recommendation-sentence/{symbol}")
def get_ai_action_recommendation_sentence(symbol: str):
    """Get AI action recommendation with reasoning for a stock."""
    logger.info("AI action recommendation sentence requested for %s", symbol)
    try:
        result = with_ai_cache("ai-action-recommendation-sentence", symbol, flow.get_ai_action_recommendation_sentence)
        logger.info("Successfully generated AI action recommendation sentence for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI action recommendation sentence for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/action-recommendation-word/{symbol}")
def get_ai_action_recommendation_single_word(symbol: str):
    """Get AI action recommendation as a single word for a stock."""
    logger.info("AI action recommendation word requested for %s", symbol)
    try:
        result = with_ai_cache("ai-action-recommendation-word", symbol, flow.get_ai_action_recommendation_single_word)
        logger.info("Successfully generated AI action recommendation word for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI action recommendation word for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/news-sentiment/{symbol}")
def get_ai_news_sentiment(symbol: str):
    """Get AI analysis of news sentiment for a stock."""
    logger.info("AI news sentiment requested for %s", symbol)
    try:
        result = with_ai_cache("ai-news-sentiment", symbol, flow.get_ai_news_sentiment)
        logger.info("Successfully generated AI news sentiment for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI news sentiment for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/full-report/{symbol}")
def get_ai_full_report(symbol: str):
    """Get comprehensive AI report for a stock."""
    logger.info("AI full report requested for %s", symbol)
    try:
        result = with_ai_cache("ai-full-report", symbol, flow.get_ai_full_report)
        logger.info("Successfully generated AI full report for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI full report for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/trading-strategy/{symbol}")
def get_trading_strategy(symbol: str):
    """Get trading strategy with entry/exit targets, stop loss, and timeframe."""
    logger.info("Trading strategy requested for %s", symbol)
    try:
        result = with_cache("trading-strategy", symbol, flow.get_trading_strategy)
        logger.info("Successfully generated trading strategy for %s", symbol)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error generating trading strategy for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
