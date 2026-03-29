#!/usr/bin/env python3
"""Load fundamental JSON files from historical_data into PostgreSQL (idempotent).

Usage:
    python scripts/load_fundamentals.py
    python scripts/load_fundamentals.py --data-dir historical_data
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "oobir"),
        user=os.environ.get("PGUSER", "oobir"),
        password=os.environ.get("PGPASSWORD", "oobir"),
    )


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


def _parse_timestamp(info: dict) -> datetime:
    """Extract or create a fetch timestamp."""
    raw = info.get("_fetched_at")
    if raw:
        return datetime.fromisoformat(raw)
    return datetime.now(timezone.utc)


def _convert_epoch(val):
    """Convert epoch seconds to datetime if applicable (e.g. exDividendDate)."""
    if isinstance(val, (int, float)) and val > 0:
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    return None


def ticker_from_filename(path: Path) -> str:
    name = path.name
    if name.endswith("_fundamentals.json"):
        return name.replace("_fundamentals.json", "")
    return path.stem


def load_file(conn, path: Path) -> int:
    ticker = ticker_from_filename(path)
    info = json.loads(path.read_text())
    fetched_at = _parse_timestamp(info)

    # Build column values
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

    sql = f"INSERT INTO fundamentals ({col_names}) VALUES ({placeholders}) ON CONFLICT (ticker, fetched_at) DO NOTHING"
    with conn.cursor() as cur:
        cur.execute(sql, vals)

    print(f"Loaded {ticker} fundamentals ({len(cols)} fields)")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load fundamental JSON data into PostgreSQL."
    )
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parent.parent / "historical_data"),
        help="Directory containing *_fundamentals.json files",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"Data dir not found: {data_dir}")

    files = sorted(data_dir.glob("*_fundamentals.json"))
    if not files:
        print(f"No fundamentals files found in {data_dir}")
        return 0

    total = 0
    conn = get_conn()
    try:
        for path in files:
            try:
                total += load_file(conn, path)
                conn.commit()
            except Exception as exc:
                conn.rollback()
                print(f"Error loading {path.name}: {exc}")
    finally:
        conn.close()

    print(f"Done. Loaded {total} fundamental snapshots.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
