"""FastAPI application exposing flow.py functions as REST endpoints.

No authentication; suitable for internal networks only.
"""

import json
import logging
import os
import math
from datetime import date, datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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

# Compress larger JSON responses to reduce page-load transfer time.
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Set Ollama host from environment or use default
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
logger.info("Ollama host configured: %s", OLLAMA_HOST)

PRICE_HISTORY_WINDOW = 121


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


def normalize_price_history_payload(payload):
    """Trim price-history payloads to the most recent chart window."""
    if isinstance(payload, list):
        return payload[-PRICE_HISTORY_WINDOW:]

    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            trimmed_data = data[-PRICE_HISTORY_WINDOW:]
            if len(trimmed_data) != len(data):
                normalized = dict(payload)
                normalized["data"] = trimmed_data
                return normalized

    return payload


def get_price_history_payload(symbol: str):
    """Return a trimmed price-history payload, caching the trimmed response."""
    cached_data = db.get_cached_data("price-history", symbol)
    if cached_data is not None:
        trimmed_cached = normalize_price_history_payload(cached_data)
        if trimmed_cached != cached_data:
            db.set_cached_data("price-history", trimmed_cached, symbol)
        return trimmed_cached

    # Prefer stored historical data from TimescaleDB, fallback to yfinance.
    try:
        conn = db_timescale.get_conn()
        try:
            db_rows = db_timescale.fetch_price_history(
                conn,
                symbol,
                limit=PRICE_HISTORY_WINDOW,
            )
        finally:
            conn.close()
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
            "DB price-history lookup failed for %s, falling back: %s",
            symbol,
            str(exc),
        )
        db_rows = []

    if db_rows:
        payload = normalize_price_history_payload({"data": serialize_value(db_rows)})
        db.set_cached_data("price-history", payload, symbol)
        return payload

    result = flow.get_price_history(symbol)
    if isinstance(result, str):
        result = json.loads(result)
    result = normalize_price_history_payload(result)
    serialized_result = serialize_value(result)
    db.set_cached_data("price-history", serialized_result, symbol)
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


def _extract_fundamentals_payload(db_result: dict | None, symbol: str) -> dict:
    """Normalize DB fundamentals row into a payload suitable for scoring."""
    if not isinstance(db_result, dict):
        return {"symbol": symbol}

    payload = db_result
    if isinstance(db_result.get("raw_info"), dict):
        payload = db_result["raw_info"]

    if "symbol" not in payload:
        payload = {**payload, "symbol": symbol}

    if "pe_ratio" not in payload:
        payload["pe_ratio"] = payload.get("trailingPE") or payload.get("trailing_pe")
    if "market_cap" not in payload:
        payload["market_cap"] = payload.get("marketCap") or payload.get("market_cap")

    return payload


def _to_float(value, default=0.0):
    """Convert to float with fallback."""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _feature_vector(payload: dict) -> dict:
    """Build normalized feature vector used by related-stock similarity."""
    current_price = _to_float(
        payload.get("currentPrice")
        or payload.get("current_price")
        or payload.get("regularMarketPrice")
    )
    previous_close = _to_float(
        payload.get("regularMarketPreviousClose")
        or payload.get("regular_market_previous_close")
        or payload.get("previousClose")
        or payload.get("previous_close")
    )
    if previous_close <= 0:
        previous_close = current_price

    volume_value = _to_float(
        payload.get("averageVolume")
        or payload.get("average_volume")
        or payload.get("averageDailyVolume10Day")
        or payload.get("average_daily_volume_10day")
        or payload.get("volume")
    )

    dividend_yield = _to_float(
        payload.get("dividendYield")
        or payload.get("dividend_yield")
        or payload.get("trailingAnnualDividendYield")
        or payload.get("trailing_annual_dividend_yield")
    )
    has_dividend = dividend_yield > 0

    change_pct = 0.0
    if previous_close > 0 and current_price > 0:
        change_pct = ((current_price - previous_close) / previous_close) * 100.0

    return {
        "price": current_price,
        "change_pct": change_pct,
        "volume": volume_value,
        "dividend_yield": dividend_yield,
        "has_dividend": has_dividend,
    }


def _similarity_score(base: dict, candidate: dict) -> float:
    """Lower score means more similar."""
    base_price = max(base.get("price", 0.0), 1e-9)
    cand_price = max(candidate.get("price", 0.0), 1e-9)
    price_distance = abs(math.log10(base_price) - math.log10(cand_price))

    change_distance = min(
        abs(base.get("change_pct", 0.0) - candidate.get("change_pct", 0.0)) / 12.0,
        3.0,
    )

    base_volume = max(base.get("volume", 0.0), 1e-9)
    cand_volume = max(candidate.get("volume", 0.0), 1e-9)
    volume_distance = abs(math.log10(base_volume) - math.log10(cand_volume))

    dividend_penalty = (
        0.0
        if base.get("has_dividend", False) == candidate.get("has_dividend", False)
        else 0.35
    )

    return (
        price_distance * 0.45
        + change_distance * 0.35
        + volume_distance * 0.15
        + dividend_penalty * 0.05
    )


def _similarity_reason(base: dict, candidate: dict) -> str:
    """Create short human-readable reason for why candidate is related."""
    reasons = []

    if abs(base.get("change_pct", 0.0) - candidate.get("change_pct", 0.0)) < 2.5:
        reasons.append("similar daily price move")

    if (
        abs(
            math.log10(max(base.get("price", 0.0), 1e-9))
            - math.log10(max(candidate.get("price", 0.0), 1e-9))
        )
        < 0.35
    ):
        reasons.append("similar price range")

    if (
        abs(
            math.log10(max(base.get("volume", 0.0), 1e-9))
            - math.log10(max(candidate.get("volume", 0.0), 1e-9))
        )
        < 0.6
    ):
        reasons.append("comparable trading volume")

    if base.get("has_dividend", False) == candidate.get("has_dividend", False):
        if base.get("has_dividend", False):
            reasons.append("both pay dividends")
        else:
            reasons.append("both are non-dividend names")

    if not reasons:
        return "overlapping price/volume profile"
    return ", ".join(reasons[:2])


def get_fundamentals_payload(symbol: str):
    """Return fundamentals payload with DB-first strategy and cache."""
    cached = db.get_cached_data("fundamentals", symbol)
    if cached is not None:
        return cached

    # Prefer stored fundamentals from TimescaleDB, fallback to yfinance.
    try:
        conn = db_timescale.get_conn()
        try:
            db_result = db_timescale.fetch_latest_fundamentals(conn, symbol)
        finally:
            conn.close()
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
            "DB fundamentals lookup failed for %s, falling back: %s",
            symbol,
            str(exc),
        )
        db_result = None

    if db_result is not None:
        payload = db_result
        if isinstance(db_result, dict) and isinstance(db_result.get("raw_info"), dict):
            payload = db_result["raw_info"]

        if isinstance(payload, dict) and "symbol" not in payload:
            payload = {**payload, "symbol": symbol}

        # Preserve legacy field aliases expected by existing clients/tests.
        if isinstance(payload, dict):
            if "pe_ratio" not in payload:
                payload["pe_ratio"] = payload.get("trailingPE") or payload.get(
                    "trailing_pe"
                )
            if "market_cap" not in payload:
                payload["market_cap"] = payload.get("marketCap") or payload.get(
                    "market_cap"
                )

        serialized = serialize_value(payload)
        db.set_cached_data("fundamentals", serialized, symbol)
        return serialized

    result = with_cache("fundamentals", symbol, flow.get_fundamentals)
    if isinstance(result, str):
        result = json.loads(result)
    return result


def get_related_stocks_payload(symbol: str, limit: int, exclude: str):
    """Return related stocks payload used by both standalone and snapshot endpoints."""
    excluded = {value.strip().upper() for value in exclude.split(",") if value.strip()}
    excluded.add(symbol)

    conn = db_timescale.get_conn()
    try:
        base_row = db_timescale.fetch_latest_fundamentals(conn, symbol)
        base_payload = _extract_fundamentals_payload(base_row, symbol)
        base_features = _feature_vector(base_payload)

        # If base ticker lacks fundamentals, fallback to flow data.
        if base_features["price"] <= 0:
            raw = flow.get_fundamentals(symbol)
            parsed = json.loads(raw) if isinstance(raw, str) else (raw or {})
            base_payload = parsed if isinstance(parsed, dict) else {"symbol": symbol}
            base_features = _feature_vector(base_payload)

        candidate_tickers = [
            ticker.upper() for ticker in db_timescale.list_fundamental_tickers(conn)
        ]
        candidate_rows = db_timescale.fetch_latest_fundamentals_bulk(
            conn,
            candidate_tickers,
        )
        scored = []

        for candidate_ticker in candidate_tickers:
            cand = candidate_ticker
            if cand in excluded:
                continue

            cand_row = candidate_rows.get(cand)
            cand_payload = _extract_fundamentals_payload(cand_row, cand)
            cand_features = _feature_vector(cand_payload)

            if cand_features["price"] <= 0:
                continue

            score = _similarity_score(base_features, cand_features)
            scored.append(
                {
                    "ticker": cand,
                    "name": cand_payload.get("shortName")
                    or cand_payload.get("longName")
                    or cand,
                    "score": round(score, 4),
                    "reason": _similarity_reason(base_features, cand_features),
                    "price": round(cand_features["price"], 2),
                    "change_pct": round(cand_features["change_pct"], 2),
                    "dividend_yield": round(cand_features["dividend_yield"] * 100.0, 2),
                    "has_dividend": cand_features["has_dividend"],
                    "link": f"index.html?ticker={cand}",
                }
            )

        scored.sort(key=lambda row: row["score"])
        result = scored[:limit]
        return {"symbol": symbol, "related": result}
    finally:
        conn.close()


def _compute_rsi(closes: list[float], period: int = 14) -> float | None:
    """Compute a simple RSI value from close prices."""
    if len(closes) < period + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(delta, 0.0) for delta in deltas]
    losses = [abs(min(delta, 0.0)) for delta in deltas]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss <= 1e-12:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _parse_portfolio_tickers(portfolio: str, symbol: str) -> list[str]:
    """Parse comma-separated portfolio tickers and exclude current symbol."""
    values = [
        item.strip().upper() for item in (portfolio or "").split(",") if item.strip()
    ]
    unique = []
    for value in values:
        if value == symbol:
            continue
        if value in unique:
            continue
        unique.append(value)
    return unique[:12]


def _extract_close_series(payload) -> list[float]:
    """Extract close price series from price-history payload."""
    rows = []
    if isinstance(payload, dict):
        rows = payload.get("data") or []
    elif isinstance(payload, list):
        rows = payload

    closes = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        close_value = _to_float(row.get("Close") or row.get("close"), default=0.0)
        if close_value > 0:
            closes.append(close_value)
    return closes


def get_decision_engine_payload(
    symbol: str, portfolio_tickers: list[str] | None = None
):
    """Build deterministic investment decision payload with risk gating."""
    fundamentals = get_fundamentals_payload(symbol)
    price_payload = get_price_history_payload(symbol)

    closes = _extract_close_series(price_payload)

    latest_price = (
        closes[-1]
        if closes
        else _to_float(
            (fundamentals or {}).get("currentPrice")
            or (fundamentals or {}).get("current_price")
            or (fundamentals or {}).get("regularMarketPrice"),
            default=0.0,
        )
    )

    momentum_5 = 0.0
    momentum_20 = 0.0
    if len(closes) >= 6 and closes[-6] > 0:
        momentum_5 = ((closes[-1] - closes[-6]) / closes[-6]) * 100.0
    if len(closes) >= 21 and closes[-21] > 0:
        momentum_20 = ((closes[-1] - closes[-21]) / closes[-21]) * 100.0

    returns: list[float] = []
    if len(closes) >= 2:
        for idx in range(1, len(closes)):
            prev = closes[idx - 1]
            curr = closes[idx]
            if prev > 0:
                returns.append((curr - prev) / prev)

    annual_vol = 0.0
    if len(returns) >= 5:
        annual_vol = float(np.std(returns) * np.sqrt(252.0))

    rsi = _compute_rsi(closes)

    pe_ratio = _to_float(
        (fundamentals or {}).get("trailingPE")
        or (fundamentals or {}).get("trailing_pe")
        or (fundamentals or {}).get("pe_ratio"),
        default=0.0,
    )
    dividend_yield = _to_float(
        (fundamentals or {}).get("dividendYield")
        or (fundamentals or {}).get("dividend_yield"),
        default=0.0,
    )
    return_on_equity = _to_float(
        (fundamentals or {}).get("returnOnEquity")
        or (fundamentals or {}).get("return_on_equity"),
        default=0.0,
    )

    momentum_score = max(-100.0, min(100.0, (momentum_20 * 3.2) + (momentum_5 * 1.4)))

    valuation_score = 0.0
    if pe_ratio > 0:
        if pe_ratio < 18:
            valuation_score = 55.0
        elif pe_ratio < 30:
            valuation_score = 20.0
        elif pe_ratio < 45:
            valuation_score = -10.0
        else:
            valuation_score = -45.0

    quality_score = max(-100.0, min(100.0, (return_on_equity - 0.12) * 500.0))
    income_score = max(-100.0, min(100.0, dividend_yield * 900.0))
    risk_score = max(-100.0, min(100.0, -annual_vol * 140.0))

    base_score = (
        momentum_score * 0.35
        + valuation_score * 0.25
        + quality_score * 0.20
        + income_score * 0.10
        + risk_score * 0.10
    )

    portfolio_tickers = portfolio_tickers or []
    sector_penalty = 0.0
    corr_penalty = 0.0
    portfolio_notes: list[str] = []

    if portfolio_tickers:
        target_sector = str(
            (fundamentals or {}).get("sector")
            or (fundamentals or {}).get("Sector")
            or ""
        )
        same_sector = 0
        max_abs_corr = 0.0

        base_returns = []
        if len(closes) >= 2:
            for idx in range(1, len(closes)):
                prev = closes[idx - 1]
                curr = closes[idx]
                if prev > 0:
                    base_returns.append((curr - prev) / prev)

        for holding in portfolio_tickers:
            try:
                h_fund = get_fundamentals_payload(holding)
                h_sector = str(
                    (h_fund or {}).get("sector") or (h_fund or {}).get("Sector") or ""
                )
                if (
                    target_sector
                    and h_sector
                    and h_sector.lower() == target_sector.lower()
                ):
                    same_sector += 1

                h_prices = _extract_close_series(get_price_history_payload(holding))
                h_returns = []
                if len(h_prices) >= 2:
                    for idx in range(1, len(h_prices)):
                        prev = h_prices[idx - 1]
                        curr = h_prices[idx]
                        if prev > 0:
                            h_returns.append((curr - prev) / prev)

                overlap = min(len(base_returns), len(h_returns), 30)
                if overlap >= 10:
                    base_slice = np.array(base_returns[-overlap:])
                    hold_slice = np.array(h_returns[-overlap:])
                    if np.std(base_slice) > 1e-12 and np.std(hold_slice) > 1e-12:
                        corr = float(np.corrcoef(base_slice, hold_slice)[0, 1])
                        if not np.isnan(corr):
                            max_abs_corr = max(max_abs_corr, abs(corr))
            except Exception:  # pylint: disable=broad-except
                continue

        if same_sector >= 2:
            sector_penalty = min(25.0, 8.0 * same_sector)
            portfolio_notes.append(
                f"Sector overlap detected with {same_sector} existing holdings."
            )

        if max_abs_corr >= 0.75:
            corr_penalty = min(25.0, (max_abs_corr - 0.75) * 100.0)
            portfolio_notes.append(
                f"High correlation to current holdings (max |rho|={max_abs_corr:.2f})."
            )

    weighted_score = base_score - sector_penalty - corr_penalty

    reason_codes: list[str] = []
    if momentum_score >= 25:
        reason_codes.append("MOMENTUM_POSITIVE")
    elif momentum_score <= -25:
        reason_codes.append("MOMENTUM_NEGATIVE")

    if valuation_score >= 30:
        reason_codes.append("VALUATION_ATTRACTIVE")
    elif valuation_score <= -20:
        reason_codes.append("VALUATION_STRETCHED")

    if quality_score >= 20:
        reason_codes.append("QUALITY_STRONG")
    elif quality_score <= -20:
        reason_codes.append("QUALITY_WEAK")

    if annual_vol >= 0.65:
        reason_codes.append("VOLATILITY_HIGH")

    risk_gates = {
        "weak_data": len(closes) < 40,
        "volatility_high": annual_vol >= 0.65,
        "valuation_stretched": pe_ratio >= 45,
        "rsi_overextended": bool(rsi is not None and (rsi >= 78 or rsi <= 22)),
    }

    confidence = 0.35
    if len(closes) >= 40:
        confidence += 0.20
    if pe_ratio > 0:
        confidence += 0.10
    if return_on_equity != 0:
        confidence += 0.10
    if abs(momentum_score) >= 25:
        confidence += 0.10
    if abs(weighted_score) >= 30:
        confidence += 0.10
    if risk_gates["volatility_high"]:
        confidence -= 0.10
    if risk_gates["weak_data"]:
        confidence -= 0.10
    if sector_penalty > 0 or corr_penalty > 0:
        confidence -= 0.08
    confidence = max(0.0, min(0.95, confidence))

    action = "WAIT"
    action_label = "WAIT"
    if not (risk_gates["weak_data"] or risk_gates["volatility_high"]):
        if weighted_score >= 25 and confidence >= 0.55:
            action = "CONSIDER_LONG"
            action_label = "CONSIDER LONG"
        elif weighted_score <= -25:
            action = "REDUCE_RISK"
            action_label = "REDUCE RISK"

    risk_notes: list[str] = []
    if risk_gates["weak_data"]:
        risk_notes.append("Limited price history; confidence reduced.")
    if risk_gates["volatility_high"]:
        risk_notes.append("Volatility is elevated; position sizing should be smaller.")
    if risk_gates["valuation_stretched"]:
        risk_notes.append("Valuation is stretched relative to baseline thresholds.")
    if risk_gates["rsi_overextended"]:
        risk_notes.append("RSI is near an extreme; pullback risk is higher.")
    risk_notes.extend(portfolio_notes)

    return {
        "symbol": symbol,
        "action": action,
        "action_label": action_label,
        "score": round(weighted_score, 2),
        "base_score": round(base_score, 2),
        "confidence": round(confidence, 2),
        "confidence_label": (
            "HIGH" if confidence >= 0.75 else "MEDIUM" if confidence >= 0.5 else "LOW"
        ),
        "risk_gates": risk_gates,
        "risk_notes": risk_notes,
        "reason_codes": reason_codes,
        "metrics": {
            "price": round(latest_price, 4),
            "momentum_5d_pct": round(momentum_5, 2),
            "momentum_20d_pct": round(momentum_20, 2),
            "annualized_volatility": round(annual_vol, 4),
            "rsi_14": round(rsi, 2) if rsi is not None else None,
            "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
            "dividend_yield": round(dividend_yield, 4) if dividend_yield else 0.0,
            "return_on_equity": (
                round(return_on_equity, 4) if return_on_equity else None
            ),
            "data_points": len(closes),
        },
        "component_scores": {
            "momentum": round(momentum_score, 2),
            "valuation": round(valuation_score, 2),
            "quality": round(quality_score, 2),
            "income": round(income_score, 2),
            "risk": round(risk_score, 2),
        },
        "portfolio_adjustments": {
            "tickers": portfolio_tickers,
            "sector_penalty": round(sector_penalty, 2),
            "correlation_penalty": round(corr_penalty, 2),
            "total_penalty": round(sector_penalty + corr_penalty, 2),
        },
    }


# ============================================================================
# Data Endpoints
# ============================================================================


@app.get("/api/fundamentals/{symbol}")
def get_fundamentals(symbol: str):
    """Get fundamentals for a given stock symbol."""
    symbol = symbol.upper()
    logger.info("Fetching fundamentals for %s", symbol)
    try:
        result = get_fundamentals_payload(symbol)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching fundamentals for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/price-history/{symbol}")
def get_price_history(symbol: str):
    """Get historical price data for a given stock symbol."""
    symbol = symbol.upper()
    logger.info("Fetching price history for %s", symbol)
    try:
        result = get_price_history_payload(symbol)
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


@app.get("/api/related-stocks/{symbol}")
def get_related_stocks(
    symbol: str,
    limit: int = Query(default=3, ge=1, le=10),
    exclude: str = "",
):
    """Get a small set of related stocks for exploration without loops.

    Relatedness is based on price level, recent % move, volume profile,
    and dividend profile similarity.
    """
    symbol = symbol.upper()
    logger.info("Fetching related stocks for %s", symbol)
    try:
        result = get_related_stocks_payload(symbol, limit, exclude)
        return JSONResponse(content=result)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error fetching related stocks for %s: %s", symbol, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/stock-snapshot/{symbol}")
def get_stock_snapshot(
    symbol: str,
    related_limit: int = Query(default=3, ge=1, le=10),
    exclude: str = "",
    portfolio: str = "",
):
    """Return a single payload for initial stock page rendering."""
    symbol = symbol.upper()
    logger.info("Fetching stock snapshot for %s", symbol)
    portfolio_tickers = _parse_portfolio_tickers(portfolio, symbol)

    snapshot = {
        "symbol": symbol,
        "fundamentals": None,
        "price_history": None,
        "news": None,
        "analyst_targets": None,
        "calendar": None,
        "option_chain": None,
        "related_stocks": None,
        "decision_engine": None,
        "section_errors": {},
    }

    section_getters = {
        "fundamentals": lambda: get_fundamentals_payload(symbol),
        "price_history": lambda: get_price_history_payload(symbol),
        "news": lambda: with_cache("news", symbol, flow.get_news),
        "analyst_targets": lambda: with_cache(
            "analyst-targets", symbol, flow.get_analyst_price_targets
        ),
        "calendar": lambda: with_cache("calendar", symbol, flow.get_calendar),
        "option_chain": lambda: serialize_value(
            with_cache("option-chain", symbol, flow.get_option_chain)
        ),
        "related_stocks": lambda: get_related_stocks_payload(
            symbol,
            related_limit,
            exclude,
        ),
        "decision_engine": lambda: get_decision_engine_payload(
            symbol, portfolio_tickers
        ),
    }

    for section, getter in section_getters.items():
        try:
            snapshot[section] = getter()
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning(
                "Snapshot section failed for %s/%s: %s",
                symbol,
                section,
                str(exc),
            )
            snapshot["section_errors"][section] = str(exc)

    return JSONResponse(content=snapshot)


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


@app.get("/api/decision-engine/{symbol}")
def get_decision_engine(symbol: str, portfolio: str = ""):
    """Return deterministic decision score with confidence and risk gates."""
    symbol = symbol.upper()
    logger.info("Decision engine requested for %s", symbol)
    try:
        payload = get_decision_engine_payload(
            symbol,
            _parse_portfolio_tickers(portfolio, symbol),
        )
        return JSONResponse(content=payload)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Decision engine error for %s: %s", symbol, str(exc))
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

    base_sql = """
        WITH latest AS (
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
            WHERE ticker IS NOT NULL
    """

    try:
        conn = db_timescale.get_conn()
        try:
            from psycopg2 import sql as psql  # pylint: disable=import-outside-toplevel
            from psycopg2.extras import (
                RealDictCursor,
            )  # pylint: disable=import-outside-toplevel

            query = psql.SQL(base_sql)
            if conditions:
                query += psql.SQL(" AND ") + psql.SQL(" AND ").join(
                    psql.SQL(condition) for condition in conditions
                )
            query += psql.SQL("""
                    ORDER BY ticker, fetched_at DESC
                )
                SELECT * FROM latest
                ORDER BY {sort_col} {sort_dir} NULLS LAST
                LIMIT %s
                """).format(
                sort_col=psql.Identifier(sort_by),
                sort_dir=psql.SQL(sort_dir.upper()),
            )

            query_params = [*params, limit]

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, query_params)
                rows = cur.fetchall()

            results = []
            for row in rows:
                d = dict(row)
                for k, v in d.items():
                    if isinstance(v, datetime):
                        d[k] = v.isoformat()
                    elif isinstance(v, (float, np.floating)) and pd.isna(v):
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

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
