#!/usr/bin/env python3
"""Load historical price JSON files into PostgreSQL/TimescaleDB (idempotent).

Usage:
    python scripts/load_historical_data.py
    python scripts/load_historical_data.py --data-dir historical_data
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

import psycopg2
from psycopg2.extras import execute_values


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "oobir"),
        user=os.environ.get("PGUSER", "oobir"),
        password=os.environ.get("PGPASSWORD", "oobir"),
    )


def extract_rows(payload: dict, ticker: str) -> list[tuple]:
    data = None
    if isinstance(payload, dict):
        data = payload.get("data") or payload.get("history") or payload.get("prices")
    if not isinstance(data, list):
        return []

    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue
        rows.append(
            (
                ticker,
                item.get("Date") or item.get("date"),
                item.get("Open") or item.get("open"),
                item.get("High") or item.get("high"),
                item.get("Low") or item.get("low"),
                item.get("Close") or item.get("close"),
                item.get("Volume") or item.get("volume"),
                item.get("Dividends") or item.get("dividends"),
                item.get("Stock Splits")
                or item.get("stock_splits")
                or item.get("StockSplits"),
            )
        )
    return rows


def ticker_from_filename(path: Path) -> str:
    name = path.name
    if name.endswith("_price_history_all.json"):
        return name.replace("_price_history_all.json", "")
    return path.stem


def iter_files(data_dir: Path) -> Iterable[Path]:
    return sorted(data_dir.glob("*_price_history_all.json"))


def load_file(conn, path: Path) -> int:
    ticker = ticker_from_filename(path)
    with conn.cursor() as cur:
        payload = json.loads(path.read_text())
        rows = extract_rows(payload, ticker)
        if not rows:
            print(f"Skip {ticker}: no rows in file")
            return 0

        sql = """
            INSERT INTO price_history
                (ticker, date, open, high, low, close, volume, dividends, stock_splits)
            VALUES %s
            ON CONFLICT (ticker, date) DO NOTHING
        """
        execute_values(cur, sql, rows, page_size=1000)
        print(f"Loaded {ticker}: {len(rows)} rows")
        return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load historical JSON data into PostgreSQL."
    )
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parent.parent / "historical_data"),
        help="Directory containing *_price_history_all.json files",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"Data dir not found: {data_dir}")

    files = list(iter_files(data_dir))
    if not files:
        print(f"No files found in {data_dir}")
        return 0

    total = 0
    with get_conn() as conn:
        for path in files:
            total += load_file(conn, path)
        conn.commit()

    print(f"Done. Inserted {total} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
