"""Training and CLI entrypoint for the ML prediction model.

Typical usage:
    python -m ml train --universe sp500
    python -m ml predict --ticker AAPL
    python -m ml backtest --ticker AAPL
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

from . import config, dataset, features, model
from .backtest import run_backtest, summarize_metrics

# Optional: pull live/yfinance data only when explicitly requested (train CLI)
# so that import-time stays dependency-light and network-free.


def _sample_universe(size: int | None, seed: int = 7) -> list[str]:
    names = dataset.ticker_filenames()
    if not size or size >= len(names):
        return names
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(names, size=size, replace=False))


def _historical_path(ticker: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "historical_data",
        f"{ticker}_price_history_all.json",
    )


def build_training_frame(
    tickers, horizon: int | None = None, live: bool = False
) -> pd.DataFrame:
    """Assemble a labelled feature frame from stored historical data.

    When ``live`` is set, tickers without a stored file are fetched from
    yfinance (5y daily) so a fresh clone can still train.
    """
    frames = []
    for ticker in tickers:
        payload = None
        path = _historical_path(ticker)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except (ValueError, OSError):
                payload = None
        if payload is None and live:
            payload = _fetch_live_payload(ticker)
        if payload is None:
            continue
        frame = dataset.labelled_frame_for_payload(payload, horizon)
        if not frame.empty:
            frame["ticker"] = ticker
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _fetch_live_payload(ticker: str):
    """Fetch a 5y daily price payload from yfinance, or None on failure."""
    try:
        import yfinance as yf

        history = yf.Ticker(ticker).history(period="5y")
        if history is None or history.empty:
            return None
        return json.loads(history.to_json(orient="table"))
    except Exception:  # pylint: disable=broad-except
        return None


def train_from_data(dataset_frame: pd.DataFrame, horizon: int | None = None):
    """Fit, print a backtest summary, and persist the model."""
    if dataset_frame.empty:
        raise SystemExit("No training data available. Check historical_data/.")

    predictor = model.train_on_frame(dataset_frame, horizon=horizon)
    path = predictor.save()
    print(f"\nSaved model -> {path}")
    print(f"Model version: {predictor.version}")
    print(f"Trained on   : {predictor.trained_on}")
    print(f"Rows         : {predictor.meta.get('rows')}")
    print(f"Classes      : {predictor.classes}")

    bt = run_backtest(dataset_frame, horizon=horizon)
    print("\n=== Walk-forward backtest ===")
    print(summarize_metrics(bt))
    return predictor


def predict_ticker(ticker: str, horizon: int | None = None, live: bool = False) -> dict:
    """Produce a prediction dict for a ticker from stored or live history."""
    path = _historical_path(ticker)
    payload = None
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    elif live:
        payload = _fetch_live_payload(ticker)
    if payload is None:
        raise FileNotFoundError(f"No stored history for {ticker}")

    frame = dataset.payload_to_frame(payload)
    return _predict_from_frame(ticker, frame, horizon)


def _predict_from_frame(ticker: str, frame, horizon: int | None = None) -> dict:
    if frame is None or len(frame) < config.MIN_HISTORY:
        raise ValueError(
            f"Insufficient history for {ticker}: need >= {config.MIN_HISTORY} rows"
        )
    predictor = model.Predictor.load()
    vector, _ = features.make_feature_vector(frame)
    probs = predictor.predict_proba(vector)
    direction = predictor.predict_direction(vector)
    low = {k.lower(): v for k, v in probs.items()}
    return {
        "symbol": ticker,
        "direction": direction,
        "probability": max(v for v in probs.values()),
        **{f"prob_{k.lower()}": v for k, v in probs.items()},
        "horizon_days": horizon if horizon is not None else config.HORIZON_DAYS,
        "confidence": predictor.confidence(
            low.get("up", 0.0), low.get("down", 0.0), low.get("flat", 0.0)
        ),
        "model_version": predictor.version,
    }


def _cli(args=None):
    parser = argparse.ArgumentParser(
        prog="ml", description="OOBIR ML price-direction tooling"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    train_p = sub.add_parser("train", help="Train and persist the model")
    train_p.add_argument(
        "--universe",
        default="sp500",
        help="ticker universe (sp500 / all / custom list)",
    )
    train_p.add_argument("--size", type=int, default=None, help="max tickers")
    train_p.add_argument("--horizon", type=int, default=None)
    train_p.add_argument("--save", action="store_true", help="persist model")
    train_p.add_argument(
        "--live", action="store_true", help="fetch missing tickers from yfinance"
    )

    predict_p = sub.add_parser("predict", help="Predict a ticker's direction")
    predict_p.add_argument("--ticker", required=True)
    predict_p.add_argument("--horizon", type=int, default=None)
    predict_p.add_argument("--live", action="store_true")

    bt_p = sub.add_parser("backtest", help="Walk-forward backtest a ticker")
    bt_p.add_argument("--ticker", required=True)
    bt_p.add_argument("--horizon", type=int, default=None)
    bt_p.add_argument("--live", action="store_true")

    args = parser.parse_args(args)

    if args.command == "train":
        names = _sample_universe(args.size)
        frame = build_training_frame(names, args.horizon, live=args.live)
        print(f"Built dataset from {len(names)} tickers: {frame.shape[0]} rows")
        predictor = train_from_data(frame, args.horizon)
        if args.save:
            predictor.save()
    elif args.command == "predict":
        result = predict_ticker(args.ticker, args.horizon, live=args.live)
        print(json.dumps(result, indent=2))
    elif args.command == "backtest":
        payload = None
        path = _historical_path(args.ticker)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        elif args.live:
            payload = _fetch_live_payload(args.ticker)
        if payload is None:
            raise SystemExit(f"No stored history for {args.ticker}")
        df = dataset.labelled_frame_for_payload(payload, args.horizon)
        metrics = run_backtest(df, horizon=args.horizon)
        print(summarize_metrics(metrics))


if __name__ == "__main__":
    _cli()
