#!/usr/bin/env python3
"""Daily market data sync job.

Pulls end-of-day price data for all tracked tickers, back-fills any gaps,
refreshes fundamentals, and recomputes technical indicators.

Designed to run once daily after market close (e.g., 6 PM ET via cron).

Usage:
    python scripts/daily_sync.py                     # sync all tracked tickers
    python scripts/daily_sync.py AAPL MSFT           # sync specific tickers only
    python scripts/daily_sync.py --prices-only       # skip fundamentals refresh
    python scripts/daily_sync.py --fundamentals-only # skip price/indicator sync
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone

import psycopg2
import yfinance as yf
from psycopg2.extras import execute_values, RealDictCursor

# ── DB connection ───────────────────────────────────────────────────────────


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "oobir"),
        user=os.environ.get("PGUSER", "oobir"),
        password=os.environ.get("PGPASSWORD", "oobir"),
    )


# ── Tracked tickers ────────────────────────────────────────────────────────


def get_tracked_tickers(conn) -> list[str]:
    """Return all tickers present in either price_history or fundamentals."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ticker FROM (
                SELECT DISTINCT ticker FROM price_history
                UNION
                SELECT DISTINCT ticker FROM fundamentals
            ) AS combined
            ORDER BY ticker
        """)
        return [r[0] for r in cur.fetchall()]


# ── Price history sync ──────────────────────────────────────────────────────


def get_last_date(conn, ticker: str) -> datetime | None:
    """Return the most recent price_history date for a ticker."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT MAX(date) FROM price_history WHERE ticker = %s",
            (ticker,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def sync_prices(conn, ticker: str) -> int:
    """Fetch missing price data from yfinance and insert into the DB.

    If no data exists yet, fetches full history (period='max').
    Otherwise, fetches from the day after the last stored date to today.
    Returns the number of new rows inserted.
    """
    last_date = get_last_date(conn, ticker)

    if last_date is None:
        # No history at all — fetch everything
        print(f"  {ticker}: no history found, fetching full history...")
        yf_obj = yf.Ticker(ticker)
        history = yf_obj.history(period="max")
    else:
        # Fetch from day after last stored date
        start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        if start >= today:
            print(
                f"  {ticker}: already up to date (last: {last_date.strftime('%Y-%m-%d')})"
            )
            return 0
        print(f"  {ticker}: fetching {start} to {today}...")
        yf_obj = yf.Ticker(ticker)
        history = yf_obj.history(start=start, end=today)

    if history is None or history.empty:
        print(f"  {ticker}: no new data returned")
        return 0

    rows = []
    for idx, row in history.iterrows():
        # idx is a Timestamp with tz info
        date = idx.to_pydatetime()
        rows.append(
            (
                ticker,
                date,
                float(row.get("Open", 0) or 0),
                float(row.get("High", 0) or 0),
                float(row.get("Low", 0) or 0),
                float(row.get("Close", 0) or 0),
                int(row.get("Volume", 0) or 0),
                float(row.get("Dividends", 0) or 0),
                float(row.get("Stock Splits", 0) or 0),
            )
        )

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
    conn.commit()

    print(f"  {ticker}: inserted {len(rows)} new price rows")
    return len(rows)


# ── Fundamentals refresh ───────────────────────────────────────────────────


# Map yfinance .info keys → DB columns
_FIELD_MAP = {
    "shortName": "short_name",
    "longName": "long_name",
    "sector": "sector",
    "industry": "industry",
    "exchange": "exchange",
    "currency": "currency",
    "marketCap": "market_cap",
    "enterpriseValue": "enterprise_value",
    "trailingPE": "trailing_pe",
    "forwardPE": "forward_pe",
    "pegRatio": "peg_ratio",
    "priceToBook": "price_to_book",
    "priceToSalesTrailing12Months": "price_to_sales",
    "enterpriseToEbitda": "enterprise_to_ebitda",
    "trailingEps": "trailing_eps",
    "forwardEps": "forward_eps",
    "profitMargins": "profit_margins",
    "operatingMargins": "operating_margins",
    "grossMargins": "gross_margins",
    "returnOnEquity": "return_on_equity",
    "returnOnAssets": "return_on_assets",
    "totalRevenue": "total_revenue",
    "revenuePerShare": "revenue_per_share",
    "revenueGrowth": "revenue_growth",
    "earningsGrowth": "earnings_growth",
    "ebitda": "ebitda",
    "netIncomeToCommon": "net_income",
    "freeCashflow": "free_cashflow",
    "operatingCashflow": "operating_cashflow",
    "totalCash": "total_cash",
    "totalDebt": "total_debt",
    "totalAssets": "total_assets",
    "bookValue": "book_value",
    "currentRatio": "current_ratio",
    "debtToEquity": "debt_to_equity",
    "dividendYield": "dividend_yield",
    "dividendRate": "dividend_rate",
    "payoutRatio": "payout_ratio",
    "exDividendDate": "ex_dividend_date",
    "currentPrice": "current_price",
    "previousClose": "previous_close",
    "fiftyTwoWeekHigh": "fifty_two_week_high",
    "fiftyTwoWeekLow": "fifty_two_week_low",
    "fiftyDayAverage": "fifty_day_average",
    "twoHundredDayAverage": "two_hundred_day_average",
    "targetHighPrice": "target_high_price",
    "targetLowPrice": "target_low_price",
    "targetMeanPrice": "target_mean_price",
    "targetMedianPrice": "target_median_price",
    "recommendationKey": "recommendation_key",
    "numberOfAnalystOpinions": "number_of_analyst_opinions",
}


def _convert_epoch(val):
    """Convert epoch seconds to datetime if applicable."""
    if isinstance(val, (int, float)) and val > 0:
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    return None


def sync_fundamentals(conn, ticker: str) -> bool:
    """Fetch current fundamentals from yfinance and upsert into the DB.

    Returns True on success.
    """
    from psycopg2.extras import Json

    try:
        yf_obj = yf.Ticker(ticker)
        info = yf_obj.info
        if not info or info.get("regularMarketPrice") is None:
            print(f"  {ticker}: no fundamental data available")
            return False
    except Exception as exc:
        print(f"  {ticker}: yfinance error — {exc}")
        return False

    fetched_at = datetime.now(timezone.utc)
    info["_fetched_at"] = fetched_at.isoformat()

    cols = ["ticker", "fetched_at", "raw_info"]
    vals = [ticker, fetched_at, Json(info)]

    for yf_key, db_col in _FIELD_MAP.items():
        val = info.get(yf_key)
        if val is None:
            continue
        if db_col == "ex_dividend_date":
            val = _convert_epoch(val)
        cols.append(db_col)
        vals.append(val)

    placeholders = ", ".join(["%s"] * len(vals))
    col_names = ", ".join(cols)

    sql = (
        f"INSERT INTO fundamentals ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT (ticker, fetched_at) DO NOTHING"
    )
    with conn.cursor() as cur:
        cur.execute(sql, vals)
    conn.commit()

    print(f"  {ticker}: fundamentals refreshed ({len(cols)} fields)")
    return True


# ── Technical indicators ───────────────────────────────────────────────────

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def recompute_indicators(conn, ticker: str) -> int:
    """Recompute technical indicators from price_history for a ticker.

    Returns the number of indicator rows upserted.
    """
    if not HAS_PANDAS:
        print(f"  {ticker}: skipping indicators (pandas not installed)")
        return 0

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT date, close, volume FROM price_history WHERE ticker = %s ORDER BY date",
            (ticker,),
        )
        price_rows = cur.fetchall()

    if len(price_rows) < 50:
        print(
            f"  {ticker}: not enough price data for indicators ({len(price_rows)} rows)"
        )
        return 0

    df = pd.DataFrame(price_rows)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)

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

    col_str = ", ".join(["ticker", "date"] + indicator_cols)
    update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in indicator_cols)
    sql = f"""
        INSERT INTO technical_indicators ({col_str})
        VALUES %s
        ON CONFLICT (ticker, date) DO UPDATE SET {update_str}
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)
    conn.commit()

    print(f"  {ticker}: {len(rows)} indicator rows upserted")
    return len(rows)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Daily market data sync — prices, fundamentals, and indicators."
    )
    parser.add_argument(
        "tickers", nargs="*", help="Specific tickers (default: all tracked)"
    )
    parser.add_argument(
        "--prices-only", action="store_true", help="Only sync price data"
    )
    parser.add_argument(
        "--fundamentals-only", action="store_true", help="Only refresh fundamentals"
    )
    args = parser.parse_args()

    conn = get_conn()
    try:
        tickers = (
            [t.upper() for t in args.tickers]
            if args.tickers
            else get_tracked_tickers(conn)
        )
        if not tickers:
            print("No tracked tickers found in the database.")
            return 0

        print(
            f"Daily sync starting for {len(tickers)} tickers at {datetime.now(timezone.utc).isoformat()}"
        )
        print(f"Tickers: {', '.join(tickers)}")
        print()

        # ── Phase 1: Price history ──────────────────────────────────────
        price_stats = {"synced": 0, "new_rows": 0, "errors": 0}
        if not args.fundamentals_only:
            print("=== Phase 1: Price History Sync ===")
            for ticker in tickers:
                try:
                    rows = sync_prices(conn, ticker)
                    if rows > 0:
                        price_stats["synced"] += 1
                        price_stats["new_rows"] += rows
                except Exception as exc:
                    price_stats["errors"] += 1
                    print(f"  {ticker}: ERROR — {exc}")
                    conn.rollback()
            print(
                f"\nPrices: {price_stats['synced']} tickers updated, "
                f"{price_stats['new_rows']} new rows, "
                f"{price_stats['errors']} errors\n"
            )

        # ── Phase 2: Fundamentals ───────────────────────────────────────
        fund_stats = {"refreshed": 0, "errors": 0}
        if not args.prices_only:
            print("=== Phase 2: Fundamentals Refresh ===")
            for ticker in tickers:
                try:
                    if sync_fundamentals(conn, ticker):
                        fund_stats["refreshed"] += 1
                except Exception as exc:
                    fund_stats["errors"] += 1
                    print(f"  {ticker}: ERROR — {exc}")
                    conn.rollback()
            print(
                f"\nFundamentals: {fund_stats['refreshed']} refreshed, "
                f"{fund_stats['errors']} errors\n"
            )

        # ── Phase 3: Technical indicators ───────────────────────────────
        ind_stats = {"computed": 0, "total_rows": 0, "errors": 0}
        if not args.fundamentals_only:
            print("=== Phase 3: Technical Indicators ===")
            for ticker in tickers:
                try:
                    n = recompute_indicators(conn, ticker)
                    if n > 0:
                        ind_stats["computed"] += 1
                        ind_stats["total_rows"] += n
                except Exception as exc:
                    ind_stats["errors"] += 1
                    print(f"  {ticker}: ERROR — {exc}")
                    conn.rollback()
            print(
                f"\nIndicators: {ind_stats['computed']} tickers computed, "
                f"{ind_stats['total_rows']} rows, "
                f"{ind_stats['errors']} errors\n"
            )

        # ── Summary ─────────────────────────────────────────────────────
        total_errors = (
            price_stats["errors"] + fund_stats["errors"] + ind_stats["errors"]
        )
        print("=" * 50)
        print(f"Daily sync completed at {datetime.now(timezone.utc).isoformat()}")
        print(f"  Tickers: {len(tickers)}")
        if not args.fundamentals_only:
            print(f"  New price rows: {price_stats['new_rows']}")
        if not args.prices_only:
            print(f"  Fundamentals refreshed: {fund_stats['refreshed']}")
        if not args.fundamentals_only:
            print(f"  Indicator tickers: {ind_stats['computed']}")
        if total_errors:
            print(f"  Errors: {total_errors}")
        print("=" * 50)

        return 1 if total_errors else 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
