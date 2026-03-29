"""TimescaleDB utilities for historical price data, fundamentals, and technical indicators."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable, Tuple

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "oobir"),
        user=os.environ.get("PGUSER", "oobir"),
        password=os.environ.get("PGPASSWORD", "oobir"),
    )


def get_ticker_date_range(conn, ticker: str) -> Tuple[datetime | None, datetime | None]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT MIN(date), MAX(date) FROM price_history WHERE ticker = %s",
            (ticker,),
        )
        row = cur.fetchone()
        return (row[0], row[1])


def insert_price_history_rows(conn, rows: Iterable[tuple]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    sql = """
        INSERT INTO price_history
            (ticker, date, open, high, low, close, volume, dividends, stock_splits)
        VALUES %s
        ON CONFLICT (ticker, date) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)
    return len(rows)


def fetch_price_history(
    conn,
    ticker: str,
    limit: int | None = None,
) -> list[dict]:
    sql = """
        SELECT date, open, high, low, close, volume, dividends, stock_splits
        FROM price_history
        WHERE ticker = %s
        ORDER BY date DESC
    """
    params = [ticker]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    rows.reverse()

    # Map to UI-friendly keys matching yfinance JSON (table orientation)
    mapped = []
    for row in rows:
        mapped.append(
            {
                "Date": row["date"].isoformat(),
                "Open": row["open"],
                "High": row["high"],
                "Low": row["low"],
                "Close": row["close"],
                "Volume": row["volume"],
                "Dividends": row["dividends"],
                "Stock Splits": row["stock_splits"],
            }
        )
    return mapped


# ── Fundamentals ────────────────────────────────────────────────────────────


def fetch_latest_fundamentals(conn, ticker: str) -> dict | None:
    """Return the most recent fundamentals snapshot for a ticker."""
    sql = """
        SELECT * FROM fundamentals
        WHERE ticker = %s
        ORDER BY fetched_at DESC
        LIMIT 1
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (ticker,))
        row = cur.fetchone()
    if row is None:
        return None
    # Convert to plain dict (RealDictRow → dict)
    result = dict(row)
    # Serialize datetime fields
    for key in ("fetched_at", "ex_dividend_date"):
        if result.get(key) is not None:
            result[key] = result[key].isoformat()
    return result


def list_fundamental_tickers(conn) -> list[str]:
    """Return all tickers that have fundamental data."""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ticker FROM fundamentals ORDER BY ticker")
        return [r[0] for r in cur.fetchall()]


# ── Technical Indicators ────────────────────────────────────────────────────


def fetch_technical_indicators(
    conn,
    ticker: str,
    limit: int | None = None,
) -> list[dict]:
    """Return technical indicators for a ticker, most recent first then reversed."""
    sql = """
        SELECT date, sma_20, sma_50, rsi_14,
               macd, macd_signal, macd_histogram,
               bb_upper, bb_middle, bb_lower,
               volume_avg_20, volume_ratio
        FROM technical_indicators
        WHERE ticker = %s
        ORDER BY date DESC
    """
    params: list = [ticker]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    rows.reverse()
    return [
        {
            "date": row["date"].isoformat(),
            "sma_20": row["sma_20"],
            "sma_50": row["sma_50"],
            "rsi_14": row["rsi_14"],
            "macd": row["macd"],
            "macd_signal": row["macd_signal"],
            "macd_histogram": row["macd_histogram"],
            "bb_upper": row["bb_upper"],
            "bb_middle": row["bb_middle"],
            "bb_lower": row["bb_lower"],
            "volume_avg_20": row["volume_avg_20"],
            "volume_ratio": row["volume_ratio"],
        }
        for row in rows
    ]


def fetch_latest_technical_indicators(conn, ticker: str) -> dict | None:
    """Return just the most recent technical indicator row."""
    rows = fetch_technical_indicators(conn, ticker, limit=1)
    return rows[0] if rows else None
