#!/usr/bin/env python3
"""Fetch fundamental data for a ticker via yfinance and save as JSON.

Usage:
    python scripts/fetch_fundamentals.py AAPL
    python scripts/fetch_fundamentals.py AAPL MSFT GOOG
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf


def fetch_fundamentals(ticker: str) -> dict:
    """Return yfinance .info dict plus a fetch timestamp."""
    yf_obj = yf.Ticker(ticker)
    info = yf_obj.info
    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"No fundamental data returned for '{ticker}'")
    info["_fetched_at"] = datetime.now(timezone.utc).isoformat()
    return info


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch fundamental data and save to historical_data folder."
    )
    parser.add_argument(
        "tickers", nargs="+", help="Ticker symbols (e.g., AAPL BTC-USD)"
    )
    args = parser.parse_args()

    output_dir = Path(__file__).resolve().parent.parent / "historical_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    successes = 0
    errors = 0

    for raw in args.tickers:
        ticker = raw.strip().upper()
        if not ticker:
            continue
        try:
            payload = fetch_fundamentals(ticker)
            output_path = output_dir / f"{ticker}_fundamentals.json"
            output_path.write_text(json.dumps(payload, indent=2))
            print(f"Saved {ticker} fundamentals to {output_path}")
            successes += 1
        except Exception as exc:
            print(f"Error fetching {ticker}: {exc}")
            errors += 1

    print(f"Fundamentals fetch summary: {successes} success, {errors} errors")
    if successes == 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
