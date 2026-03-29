"""FastAPI application exposing flow.py functions as REST endpoints.

No authentication; suitable for internal networks only.
"""

import os
import json
import logging
from datetime import date, datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import flow
import db  # Database caching layer
import db_timescale


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
    if hasattr(obj, "isoformat"):  # pandas Timestamp, datetime-like
        return obj.isoformat()
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    return obj


# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize and cleanup services for app lifecycle."""
    logger.info("Starting OOBIR API...")
    logger.info("Database cache initialized")
    yield
    logger.info("Shutting down OOBIR API...")


# Initialize FastAPI app
app = FastAPI(
    title="OOBIR Stock Analysis API",
    description="REST API for stock analysis and AI recommendations",
    version="1.0.0",
    lifespan=lifespan,
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
    allow_headers=["*"],
)

# Set Ollama host from environment or use default
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
logger.info("Ollama host configured: %s", OLLAMA_HOST)


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


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "OOBIR Stock Analysis API",
        "docs": "/docs",
        "redoc": "/redoc",
        "ollama_host": OLLAMA_HOST,
    }


@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "oobir-api",
        "ollama_configured": OLLAMA_HOST,
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
                "ollama_response_code": 200,
            }
        logger.warning("Ollama returned non-200: %s", response.status_code)
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "ollama_host": OLLAMA_HOST,
                "ollama_reachable": True,
                "ollama_response_code": response.status_code,
                "error": "Ollama returned unexpected status code",
            },
        )
    except requests.exceptions.Timeout:  # pylint: disable=broad-except
        logger.error("Ollama health check timeout: %s", OLLAMA_HOST)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "ollama_host": OLLAMA_HOST,
                "ollama_reachable": False,
                "error": "Timeout connecting to Ollama",
            },
        )
    except requests.exceptions.ConnectionError as exc:
        logger.error("Ollama health check connection error: %s", str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "ollama_host": OLLAMA_HOST,
                "ollama_reachable": False,
                "error": f"Cannot connect to Ollama: {str(exc)}",
            },
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Ollama health check failed: %s", str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "ollama_host": OLLAMA_HOST,
                "error": str(exc),
            },
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
            detail="AI service unavailable - Ollama connection failed or returned no response",
        ) from None

    # AI functions return plain strings, not JSON strings
    # Only attempt JSON parsing if it looks like JSON (starts with { or [)
    if isinstance(result, str) and result.strip().startswith(("{", "[")):
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
        return JSONResponse(
            content={
                "symbol": symbol,
                "deleted_entries": deleted_count,
                "message": f"Cleared {deleted_count} cache entries for {symbol}",
            }
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error clearing cache for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/api/cache/expired")
def clear_expired_cache():
    """Clear all expired cache entries."""
    logger.info("Clearing expired cache entries")
    try:
        deleted_count = db.clear_expired_cache()
        return JSONResponse(
            content={
                "deleted_entries": deleted_count,
                "message": f"Cleared {deleted_count} expired cache entries",
            }
        )
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
        result = with_ai_cache(
            "ai-fundamental-analysis", symbol, flow.get_ai_fundamental_analysis
        )
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
        result = with_ai_cache(
            "ai-balance-sheet-analysis", symbol, flow.get_ai_balance_sheet_analysis
        )
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
        result = with_ai_cache(
            "ai-income-stmt-analysis", symbol, flow.get_ai_quarterly_income_stm_analysis
        )
        logger.info(
            "Successfully generated AI income statement analysis for %s", symbol
        )
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "Error in AI income statement analysis for %s: %s", symbol, str(exc)
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/technical-analysis/{symbol}")
def get_ai_technical_analysis(symbol: str):
    """Get AI technical analysis for a stock."""
    logger.info("AI technical analysis requested for %s", symbol)
    try:
        result = with_ai_cache(
            "ai-technical-analysis", symbol, flow.get_ai_technical_analysis
        )
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
        result = with_ai_cache(
            "ai-action-recommendation", symbol, flow.get_ai_action_recommendation
        )
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
        result = with_ai_cache(
            "ai-action-recommendation-sentence",
            symbol,
            flow.get_ai_action_recommendation_sentence,
        )
        logger.info(
            "Successfully generated AI action recommendation sentence for %s", symbol
        )
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "Error in AI action recommendation sentence for %s: %s", symbol, str(exc)
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/action-recommendation-word/{symbol}")
def get_ai_action_recommendation_single_word(symbol: str):
    """Get AI action recommendation as a single word for a stock."""
    logger.info("AI action recommendation word requested for %s", symbol)
    try:
        result = with_ai_cache(
            "ai-action-recommendation-word",
            symbol,
            flow.get_ai_action_recommendation_single_word,
        )
        logger.info(
            "Successfully generated AI action recommendation word for %s", symbol
        )
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "Error in AI action recommendation word for %s: %s", symbol, str(exc)
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/ai/news-sentiment/{symbol}")
def get_ai_news_sentiment(symbol: str):
    """Get AI analysis of news sentiment for a stock.

    Times out after 30 seconds to prevent hanging.
    """
    import concurrent.futures

    logger.info("AI news sentiment requested for %s", symbol)
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                with_ai_cache, "ai-news-sentiment", symbol, flow.get_ai_news_sentiment
            )
            try:
                result = future.result(timeout=30)
                logger.info("Successfully generated AI news sentiment for %s", symbol)
                return JSONResponse(content=result)
            except concurrent.futures.TimeoutError:
                logger.warning("News sentiment analysis timed out for %s", symbol)
                raise HTTPException(
                    status_code=504,
                    detail="News sentiment analysis timed out. Please try again.",
                ) from None
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


# ── Fundamental Screener Endpoints ──────────────────────────────────────────


@app.get("/api/fundamentals-db")
def list_fundamentals_db(
    sector: str = None,
    min_market_cap: float = None,
    max_pe: float = None,
    min_dividend_yield: float = None,
    min_roe: float = None,
    max_debt_to_equity: float = None,
    sort_by: str = "market_cap",
    sort_dir: str = "desc",
    limit: int = 100,
):
    """Search and filter stocks by fundamental metrics stored in the database."""
    logger.info("Fundamental screener query: sector=%s sort=%s", sector, sort_by)

    allowed_sort_cols = {
        "market_cap",
        "trailing_pe",
        "forward_pe",
        "dividend_yield",
        "return_on_equity",
        "profit_margins",
        "revenue_growth",
        "debt_to_equity",
        "current_price",
        "ticker",
        "peg_ratio",
        "price_to_book",
        "earnings_growth",
        "free_cashflow",
    }
    if sort_by not in allowed_sort_cols:
        sort_by = "market_cap"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"
    if limit < 1 or limit > 500:
        limit = 100

    # Build query with filters
    conditions = []
    params: list = []

    if sector:
        conditions.append("sector = %s")
        params.append(sector)
    if min_market_cap is not None:
        conditions.append("market_cap >= %s")
        params.append(min_market_cap)
    if max_pe is not None:
        conditions.append("trailing_pe <= %s AND trailing_pe > 0")
        params.append(max_pe)
    if min_dividend_yield is not None:
        conditions.append("dividend_yield >= %s")
        params.append(min_dividend_yield)
    if min_roe is not None:
        conditions.append("return_on_equity >= %s")
        params.append(min_roe)
    if max_debt_to_equity is not None:
        conditions.append("debt_to_equity <= %s")
        params.append(max_debt_to_equity)

    where = ""
    if conditions:
        where = "AND " + " AND ".join(conditions)

    sql = f"""
        SELECT DISTINCT ON (ticker)
            ticker, short_name, long_name, sector, industry, exchange, currency,
            market_cap, enterprise_value,
            trailing_pe, forward_pe, peg_ratio, price_to_book, price_to_sales,
            trailing_eps, forward_eps,
            profit_margins, operating_margins, gross_margins,
            return_on_equity, return_on_assets,
            total_revenue, revenue_growth, earnings_growth,
            ebitda, free_cashflow,
            total_cash, total_debt, current_ratio, debt_to_equity,
            dividend_yield, dividend_rate, payout_ratio,
            current_price, previous_close,
            fifty_two_week_high, fifty_two_week_low,
            fifty_day_average, two_hundred_day_average,
            target_mean_price, recommendation_key, number_of_analyst_opinions,
            fetched_at
        FROM fundamentals
        WHERE ticker IS NOT NULL {where}
        ORDER BY ticker, fetched_at DESC
    """

    try:
        conn = db_timescale.get_conn()
        try:
            from psycopg2.extras import (
                RealDictCursor,
            )  # pylint: disable=import-outside-toplevel

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

            # Post-query sort (since DISTINCT ON forces ORDER BY ticker first)
            def sort_key(r):
                v = r.get(sort_by)
                if v is None:
                    return float("-inf") if sort_dir == "desc" else float("inf")
                return v

            rows.sort(key=sort_key, reverse=(sort_dir == "desc"))
            rows = rows[:limit]

            results = []
            for row in rows:
                d = dict(row)
                for k, v in d.items():
                    if isinstance(v, datetime):
                        d[k] = v.isoformat()
                    elif isinstance(v, (float,)) and (v != v):  # NaN check
                        d[k] = None
                results.append(d)

            return JSONResponse(content={"count": len(results), "results": results})
        finally:
            conn.close()
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Fundamental screener error: %s", str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/fundamentals-db/sectors")
def list_sectors():
    """Return distinct sectors from the fundamentals database."""
    try:
        conn = db_timescale.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT sector FROM fundamentals WHERE sector IS NOT NULL ORDER BY sector"
                )
                sectors = [r[0] for r in cur.fetchall()]
            return JSONResponse(content={"sectors": sectors})
        finally:
            conn.close()
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error listing sectors: %s", str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/fundamentals-db/{symbol}")
def get_fundamentals_db(symbol: str):
    """Get stored fundamental data for a specific ticker."""
    logger.info("DB fundamentals requested for %s", symbol)
    try:
        conn = db_timescale.get_conn()
        try:
            result = db_timescale.fetch_latest_fundamentals(conn, symbol.upper())
            if result is None:
                raise HTTPException(
                    status_code=404, detail=f"No fundamental data for {symbol}"
                )
            return JSONResponse(content=result)
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching DB fundamentals for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/db/stats")
def get_db_stats():
    """Return data freshness and row counts for all TimescaleDB tables."""
    try:
        conn = db_timescale.get_conn()
        try:
            from psycopg2.extras import (
                RealDictCursor,
            )  # pylint: disable=import-outside-toplevel

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) AS total_rows,
                        COUNT(DISTINCT ticker) AS tickers,
                        MAX(date)::date AS most_recent_date,
                        MIN(date)::date AS oldest_date
                    FROM price_history
                """)
                ph = dict(cur.fetchone())

                cur.execute("""
                    SELECT
                        COUNT(*) AS total_rows,
                        COUNT(DISTINCT ticker) AS tickers,
                        MAX(fetched_at) AS last_fetched
                    FROM fundamentals
                """)
                fu = dict(cur.fetchone())

                cur.execute("""
                    SELECT
                        COUNT(*) AS total_rows,
                        COUNT(DISTINCT ticker) AS tickers,
                        MAX(date)::date AS most_recent_date
                    FROM technical_indicators
                """)
                ti = dict(cur.fetchone())

                cur.execute("""
                    SELECT ticker, MAX(date)::date AS last_date
                    FROM price_history
                    GROUP BY ticker
                    ORDER BY last_date ASC
                    LIMIT 5
                """)
                stale = [dict(r) for r in cur.fetchall()]

            # Serialize datetimes
            for d in [ph, fu, ti]:
                for k, v in d.items():
                    if isinstance(v, datetime):
                        d[k] = v.isoformat()
                    elif hasattr(v, "isoformat"):
                        d[k] = v.isoformat()
            for row in stale:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()

            return JSONResponse(
                content={
                    "price_history": {
                        k: int(v) if isinstance(v, int) else v for k, v in ph.items()
                    },
                    "fundamentals": {
                        k: int(v) if isinstance(v, int) else v for k, v in fu.items()
                    },
                    "technical_indicators": {
                        k: int(v) if isinstance(v, int) else v for k, v in ti.items()
                    },
                    "stalest_tickers": stale,
                }
            )
        finally:
            conn.close()
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("DB stats error: %s", str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
