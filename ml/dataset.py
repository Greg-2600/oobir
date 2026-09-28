"""Dataset assembly -- turn per-ticker price history into a training matrix.

Accepts price history in any of the formats produced by the OOBIR stack
(yfinance table string, ``get_price_history_payload`` dict, or the
``historical_data/*_price_history_all.json`` files) and yields a labelled
feature frame.
"""

from __future__ import annotations

import json
import os
from glob import glob

import pandas as pd

from . import config, labels


def payload_to_frame(payload) -> pd.DataFrame | None:
    """Normalize a price-history payload into a sorted OHLCV DataFrame."""
    if payload is None:
        return None
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError):
            return None

    if isinstance(payload, dict):
        data = payload.get("data")
        if data is not None:
            records = data
        else:
            records = payload.get("rows") or None
        if records is None:
            return None
    elif isinstance(payload, (list, tuple)):
        records = payload
    else:
        return None

    if not records:
        return None

    df = pd.DataFrame(records)
    if "Close" not in df.columns:
        return None

    df = df.sort_values("Date" if "Date" in df.columns else df.index)
    df = df.reset_index(drop=True)
    return df


def labelled_frame_for_payload(payload, horizon: int | None = None) -> pd.DataFrame:
    """Return the labelled feature matrix for one ticker's price payload."""
    frame = payload_to_frame(payload)
    if frame is None or len(frame) < config.MIN_HISTORY:
        return pd.DataFrame()
    return labels.build_labelled_frame(frame, horizon)


def historical_files() -> list[str]:
    """Return paths to any stored full price-history JSON files."""
    return glob(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "historical_data",
            "*_price_history_all.json",
        )
    )


def ticker_filenames() -> list[str]:
    """Return tickers available from the S&P lists and historical files."""
    tickers: dict[str, None] = {}
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("sp500_tickers.txt", "sp500_missing_tickers.txt"):
        path = os.path.join(base, name)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                token = line.strip()
                if token:
                    tickers[token] = None
    for fpath in historical_files():
        name = os.path.basename(fpath)
        ticker = name.replace("_price_history_all.json", "")
        if ticker:
            tickers[ticker] = None
    return list(tickers)
