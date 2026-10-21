"""Labeling -- turn forward returns into classification targets.

Each row ``t`` is labelled by the sign of the realized forward return
``Close[t + horizon] / Close[t] - 1`` relative to a symmetric margin.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def label_forward_returns(
    price_df: pd.DataFrame, horizon: int | None = None, margin: float | None = None
) -> pd.Series:
    """Return a target Series (UP/FLAT/DOWN) aligned to feature rows.

    The result is aligned to the rows produced by :mod:`ml.features` so it can
    be ``concat``-ed into a training matrix. Rows without a future close at
    ``horizon`` are dropped by the caller.
    """
    horizon = horizon if horizon is not None else config.HORIZON_DAYS
    margin = config.MARGIN if margin is None else margin
    close = price_df["Close"].astype(float)

    future_close = close.shift(-horizon)
    forward_return = future_close / close - 1.0

    labels = pd.Series(index=price_df.index, dtype="str")
    labels[forward_return > margin] = "UP"
    labels[forward_return < -margin] = "DOWN"
    if margin > 0:
        labels[(forward_return >= -margin) & (forward_return <= margin)] = "FLAT"
    else:
        # With no dead-band, exact-zero returns count as DOWN (never FLAT),
        # avoiding a degenerate near-empty class.
        labels[forward_return == 0] = "DOWN"
    labels[future_close.isna()] = None

    return labels


def build_labelled_frame(
    price_df: pd.DataFrame,
    horizon: int | None = None,
    margin: float | None = None,
    feature_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Build a feature/label DataFrame ready for training.

    Returns a DataFrame with the feature columns plus a ``target`` column and a
    ``Date`` column, dropping warm-up and un-resolvable rows.
    """
    horizon = horizon if horizon is not None else config.HORIZON_DAYS
    indicators = compute_feature_rows(price_df, feature_columns)
    if indicators.empty:
        return pd.DataFrame()

    labels = label_forward_returns(price_df, horizon, margin).loc[indicators.index]
    frame = indicators.copy()
    frame["target"] = labels
    frame = frame.dropna(subset=["target"])

    # Drop rows where any selected feature is non-finite (e.g. zero-range BB).
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=[c for c in frame.columns if c != "target"])

    if "Date" in price_df.columns:
        dates = pd.to_datetime(price_df["Date"]).loc[frame.index]
        frame["Date"] = dates.values
    else:
        frame["Date"] = frame.index

    return frame


def compute_feature_rows(
    price_df: pd.DataFrame, feature_columns: list[str] | None = None
) -> pd.DataFrame:
    """Alias for :func:`ml.features.compute_indicators` with column selection."""
    from .features import compute_indicators, resolve_feature_columns

    frame = compute_indicators(price_df)
    cols = resolve_feature_columns(feature_columns)
    cols = [c for c in cols if c in frame.columns]
    if not cols:
        return pd.DataFrame()
    return frame[cols]
