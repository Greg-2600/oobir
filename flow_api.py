"""FastAPI application exposing flow.py functions as REST endpoints.

No authentication; suitable for internal networks only.
"""

import os
import logging
from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import flow

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


# ============================================================================
# Data Endpoints
# ============================================================================

@app.get("/api/fundamentals/{symbol}")
def get_fundamentals(symbol: str):
    """Get fundamentals for a given stock symbol."""
    logger.info("Fetching fundamentals for %s", symbol)
    try:
        result = flow.get_fundamentals(symbol)
        logger.info("Successfully fetched fundamentals for %s", symbol)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching fundamentals for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/price-history/{symbol}")
def get_price_history(symbol: str):
    """Get historical price data for a stock."""
    try:
        result = flow.get_price_history(symbol)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/analyst-targets/{symbol}")
def get_analyst_price_targets(symbol: str):
    """Get analyst price targets for a stock."""
    try:
        # `flow` exposes `get_analyst_price_targets`; call that and return
        # serializable data
        result = flow.get_analyst_price_targets(symbol)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/calendar/{symbol}")
def get_calendar(symbol: str):
    """Get events calendar for a stock."""
    try:
        result = flow.get_calendar(symbol)
        result = serialize_value(result)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/income-stmt/{symbol}")
def get_quarterly_income_stmt(symbol: str):
    """Get quarterly income statement for a stock."""
    try:
        result = flow.get_quarterly_income_stmt(symbol)
        result = serialize_value(result)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/balance-sheet/{symbol}")
def get_balance_sheet(symbol: str):
    """Get balance sheet for a stock."""
    try:
        result = flow.get_balance_sheet(symbol)
        result = serialize_value(result)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/option-chain/{symbol}")
def get_option_chain(symbol: str):
    """Get option chain for a stock."""
    try:
        result = flow.get_option_chain(symbol)
        result = serialize_value(result)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/news/{symbol}")
def get_news(symbol: str):
    """Get recent news for a stock."""
    try:
        result = flow.get_news(symbol)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/screen-undervalued")
def get_screen_undervalued_large_caps():
    """Get screen of undervalued large cap stocks."""
    try:
        result = flow.get_screen_undervalued_large_caps()
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ============================================================================
# AI Analysis Endpoints (requires Ollama)
# ============================================================================

@app.get("/api/ai/fundamental-analysis/{symbol}")
def get_ai_fundamental_analysis(symbol: str):
    """Get AI analysis of fundamentals for a stock."""
    logger.info("AI fundamental analysis requested for %s", symbol)
    try:
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_fundamental_analysis(symbol)
        if result is None:
            logger.error("AI analysis returned None for %s - Ollama may be unreachable", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_balance_sheet_analysis(symbol)
        if result is None:
            logger.error("AI balance sheet analysis returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_quarterly_income_stm_analysis(symbol)
        if result is None:
            logger.error("AI income statement analysis returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_technical_analysis(symbol)
        if result is None:
            logger.error("AI technical analysis returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_action_recommendation(symbol)
        if result is None:
            logger.error("AI action recommendation returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_action_recommendation_sentence(symbol)
        if result is None:
            logger.error("AI action recommendation sentence returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_action_recommendation_single_word(symbol)
        if result is None:
            logger.error("AI action recommendation word returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_news_sentiment(symbol)
        if result is None:
            logger.error("AI news sentiment returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
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
        flow.ensure_ollama(OLLAMA_HOST)
        result = flow.get_ai_full_report(symbol)
        if result is None:
            logger.error("AI full report returned None for %s", symbol)
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable - Ollama connection failed or returned no response"
            ) from None
        logger.info("Successfully generated AI full report for %s", symbol)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error in AI full report for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
