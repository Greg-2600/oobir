"""Feature engineering for the ML price-direction model.

Produces a numeric DataFrame of technical features computed strictly from
information available at each row ``t`` (rolling/lag windows only), so there is
no look-ahead leakage. Indicator formulas mirror ``flow._calculate_technical_
indicators`` but return values instead of prose.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Feature columns produced by compute_indicators, in stable order.
FEATURE_COLUMNS = [
    "ret_1",
    "ret_5",
    "ret_10",
    "log_ret_1",
    "volatility_10",
    "volatility_20",
    "volume_zscore_20",
    "SMA_20",
    "SMA_50",
    "close_sma20_gap",
    "close_sma50_gap",
    "RSI_14",
    "BB_percent_b",
    "MACD",
    "MACD_Signal",
    "MACD_hist",
    "return_std_10",
]

# Logical feature families so the lab can toggle whole groups of signals.
FEATURE_GROUPS = {
    "returns": ["ret_1", "ret_5", "ret_10", "log_ret_1"],
    "volatility": ["volatility_10", "volatility_20", "return_std_10"],
    "volume": ["volume_zscore_20"],
    "trend": ["SMA_20", "SMA_50", "close_sma20_gap", "close_sma50_gap"],
    "rsi": ["RSI_14"],
    "bollinger": ["BB_percent_b"],
    "macd": ["MACD", "MACD_Signal", "MACD_hist"],
}

DEFAULT_FEATURE_GROUPS = list(FEATURE_GROUPS.keys())


def resolve_feature_columns(groups: list[str] | None = None) -> list[str]:
    """Return an ordered, de-duplicated feature list for the given groups.

    ``None`` or an empty selection resolves to every feature column. Unknown
    group names are ignored.
    """
    if not groups:
        return list(FEATURE_COLUMNS)
    selected: list[str] = []
    for name in groups:
        for col in FEATURE_GROUPS.get(name, []):
            if col not in selected:
                selected.append(col)
    if not selected:
        return list(FEATURE_COLUMNS)
    # Preserve the canonical FEATURE_COLUMNS ordering for stable models.
    return [c for c in FEATURE_COLUMNS if c in selected]


def _compute_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=window).mean()
    rs = gain / loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def compute_indicators(price_df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of trailing technical features (no future data).

    Assumes ``price_df`` has the columns produced by yfinance: ``Close``,
    ``Volume`` (plus optional ``Date``/``Open``/``High``/``Low``). The returned
    DataFrame is indexed like the input and drops warm-up rows where features
    are not yet well defined.
    """
    if price_df is None or price_df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    close = price_df["Close"].astype(float)
    volume = price_df["Volume"].astype(float)

    frame = pd.DataFrame(index=price_df.index)

    # Return-based features (lagged, no future info).
    frame["ret_1"] = close.pct_change(1)
    frame["ret_5"] = close.pct_change(5)
    frame["ret_10"] = close.pct_change(10)
    frame["log_ret_1"] = np.log(close / close.shift(1))

    # Volatility / dispersion.
    frame["volatility_10"] = frame["log_ret_1"].rolling(10).std()
    frame["volatility_20"] = frame["log_ret_1"].rolling(20).std()
    frame["return_std_10"] = frame["ret_1"].rolling(10).std()

    # Volume.
    vol_mean = volume.rolling(20).mean()
    frame["volume_zscore_20"] = (volume / vol_mean) - 1.0

    # Moving averages.
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    frame["SMA_20"] = sma_20
    frame["SMA_50"] = sma_50
    frame["close_sma20_gap"] = (close - sma_20) / sma_20
    frame["close_sma50_gap"] = (close - sma_50) / sma_50

    # RSI.
    frame["RSI_14"] = _compute_rsi(close, 14)

    # Bollinger %B.
    bb_std = close.rolling(20).std()
    bb_upper = sma_20 + (bb_std * 2.0)
    bb_lower = sma_20 - (bb_std * 2.0)
    frame["BB_percent_b"] = (close - bb_lower) / (bb_upper - bb_lower)

    # MACD.
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    frame["MACD"] = ema_12 - ema_26
    frame["MACD_Signal"] = frame["MACD"].ewm(span=9, adjust=False).mean()
    frame["MACD_hist"] = frame["MACD"] - frame["MACD_Signal"]

    # Drop warm-up rows containing NaN (need >= 50 rows of history).
    return frame[FEATURE_COLUMNS].dropna()


def make_feature_vector(
    price_df: pd.DataFrame,
) -> tuple[list[float], pd.DataFrame | None]:
    """Build the latest feature vector for inference.

    Returns ``(feature_values, frame)`` where ``feature_values`` is a flat list
    aligned to ``FEATURE_COLUMNS`` and ``frame`` is the full computed frame for
    the latest row (or ``None`` when there is insufficient history).
    """
    indicators = compute_indicators(price_df)
    if indicators.empty:
        return [], None
    latest = indicators.iloc[-1]
    return [float(v) for v in latest], indicators.iloc[[-1]]
