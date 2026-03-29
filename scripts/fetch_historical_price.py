#!/usr/bin/env python3
"""Fetch full historical price data for a ticker and save as JSON.

Usage:
    python scripts/fetch_historical_price.py AAPL
    python scripts/fetch_historical_price.py AAPL MSFT GOOG
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yfinance as yf


def fetch_history(ticker: str) -> dict:
    """Return full historical price data in pandas 'table' JSON format."""
    yf_obj = yf.Ticker(ticker)
    history = yf_obj.history(period="max")
    if history is None or history.empty:
        raise ValueError(f"No historical data returned for ticker '{ticker}'")
    return json.loads(history.to_json(orient="table"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch full historical price data and save to historical_data folder."
    )
    parser.add_argument(
        "tickers", nargs="+", help="Ticker symbols (e.g., AAPL BTC-USD)"
    )
    args = parser.parse_args()

    output_dir = Path(__file__).resolve().parent.parent / "historical_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    for raw in args.tickers:
        ticker = raw.strip().upper()
        if not ticker:
            continue
        try:
            output_path = output_dir / f"{ticker}_price_history_all.json"
            payload = fetch_history(ticker)
            output_path.write_text(json.dumps(payload, indent=2))
            print(
                f"Saved {ticker} history ({len(payload.get('data', []))} rows) to {output_path}"
            )
        except Exception as exc:
            print(f"Error fetching {ticker}: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
