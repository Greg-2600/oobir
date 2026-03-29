#!/usr/bin/env python3
"""Compute technical indicators from price_history and store in technical_indicators table.

Reads OHLCV data from price_history, computes SMA, RSI, MACD, Bollinger Bands,
and volume metrics, then inserts the results.

Usage:
    python scripts/compute_technical_indicators.py              # all tickers
    python scripts/compute_technical_indicators.py AAPL MSFT    # specific tickers
"""

from __future__ import annotations

import argparse
import os

import pandas as pd
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


def get_tickers(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ticker FROM price_history ORDER BY ticker")
        return [r[0] for r in cur.fetchall()]


def fetch_prices(conn, ticker: str) -> pd.DataFrame:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT date, close, volume FROM price_history WHERE ticker = %s ORDER BY date",
            (ticker,),
        )
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def compute(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicator columns to a price DataFrame."""
    # SMA
    df["sma_20"] = df["close"].rolling(window=20).mean()
    df["sma_50"] = df["close"].rolling(window=50).mean()

    # RSI (14-period)
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = df["close"].ewm(span=12).mean()
    ema_26 = df["close"].ewm(span=26).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_histogram"] = df["macd"] - df["macd_signal"]

    # Bollinger Bands (20, 2)
    df["bb_middle"] = df["close"].rolling(window=20).mean()
    bb_std = df["close"].rolling(window=20).std()
    df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
    df["bb_lower"] = df["bb_middle"] - (bb_std * 2)

    # Volume
    df["volume_avg_20"] = df["volume"].rolling(window=20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_avg_20"]

    return df


def store_indicators(conn, ticker: str, df: pd.DataFrame) -> int:
    indicator_cols = [
        "sma_20",
        "sma_50",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_histogram",
        "bb_upper",
        "bb_middle",
        "bb_lower",
        "volume_avg_20",
        "volume_ratio",
    ]
    rows = []
    for _, row in df.iterrows():
        if pd.isna(row["sma_20"]):
            continue
        vals = [ticker, row["date"]]
        for col in indicator_cols:
            v = row[col]
            vals.append(None if pd.isna(v) else float(v))
        rows.append(tuple(vals))

    if not rows:
        return 0

    cols = ", ".join(["ticker", "date"] + indicator_cols)
    sql = f"""
        INSERT INTO technical_indicators ({cols})
        VALUES %s
        ON CONFLICT (ticker, date) DO UPDATE SET
            sma_20 = EXCLUDED.sma_20,
            sma_50 = EXCLUDED.sma_50,
            rsi_14 = EXCLUDED.rsi_14,
            macd = EXCLUDED.macd,
            macd_signal = EXCLUDED.macd_signal,
            macd_histogram = EXCLUDED.macd_histogram,
            bb_upper = EXCLUDED.bb_upper,
            bb_middle = EXCLUDED.bb_middle,
            bb_lower = EXCLUDED.bb_lower,
            volume_avg_20 = EXCLUDED.volume_avg_20,
            volume_ratio = EXCLUDED.volume_ratio
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute technical indicators from price_history."
    )
    parser.add_argument("tickers", nargs="*", help="Specific tickers (default: all)")
    args = parser.parse_args()

    with get_conn() as conn:
        tickers = args.tickers if args.tickers else get_tickers(conn)
        if not tickers:
            print("No tickers found in price_history.")
            return 0

        total = 0
        for ticker in tickers:
            ticker = ticker.upper()
            df = fetch_prices(conn, ticker)
            if df.empty:
                print(f"Skip {ticker}: no price data")
                continue
            df = compute(df)
            n = store_indicators(conn, ticker, df)
            print(f"{ticker}: {n} indicator rows")
            total += n

        conn.commit()
        print(f"Done. Stored {total} total indicator rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
