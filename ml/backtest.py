"""Walk-forward backtesting for the ML model.

Splits a labelled feature frame into expanding-train / rolling-test windows
ordered by ``Date`` and reports classification metrics plus a naive
(majority-class) baseline for comparison.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, features
from .model import build_estimator, fast_estimator


def run_backtest(
    frame: pd.DataFrame,
    horizon: int | None = None,
    folds: int | None = None,
    model_name: str | None = None,
    feature_columns: list[str] | None = None,
    max_train: int | None = None,
    min_train: int | None = None,
) -> dict:
    """Run a walk-forward backtest and return a metrics summary dict."""
    if frame is None or frame.empty:
        return _empty_metrics()

    horizon = horizon if horizon is not None else config.HORIZON_DAYS
    folds = max(1, folds if folds is not None else config.BACKTEST_FOLDS)
    min_train = min_train if min_train is not None else config.BACKTEST_MIN_TRAIN
    max_train = max_train if max_train is not None else config.BACKTEST_MAX_TRAIN

    # Order by time deterministically so walk-forward is honest even when a
    # multi-ticker frame is passed in.
    indexed = frame.reset_index(drop=True)
    if "Date" in indexed.columns:
        indexed = indexed.sort_values("Date").reset_index(drop=True)
    n = len(indexed)
    if n < min_train + 10:
        return _empty_metrics("Insufficient data for backtest")

    feature_cols = [
        c for c in (feature_columns or features.FEATURE_COLUMNS) if c in indexed.columns
    ]
    if not feature_cols:
        return _empty_metrics("No feature columns available")

    y_true: list[str] = []
    y_pred: list[str] = []

    step = int((n - min_train) // folds)
    if step <= 0:
        step = max(1, (n - min_train) // max(folds, 1))

    use_fast = model_name in (None, "hist_gbm")
    train_end = min_train
    while train_end < n:
        test_start = train_end
        test_end = min(n, test_start + step)
        if test_end <= test_start:
            break

        train = indexed.iloc[:train_end]
        # Cap the training window so each fold stays cheap on long histories.
        if max_train and len(train) > max_train:
            train = train.iloc[-max_train:]
        test = indexed.iloc[test_start:test_end]

        estimator = fast_estimator() if use_fast else build_estimator(model_name)
        estimator.fit(train[feature_cols], train["target"].astype(str))
        preds = estimator.predict(test[feature_cols])
        y_true.extend(test["target"].astype(str).tolist())
        y_pred.extend(preds.tolist())
        train_end = test_end

    result = _score(y_true, y_pred, horizon)
    result["model_name"] = model_name or "hist_gbm"
    result["folds"] = folds
    result["n_features"] = len(feature_cols)
    return result


def _score(y_true: list[str], y_pred: list[str], horizon: int) -> dict:
    if not y_true:
        return _empty_metrics()

    accuracy = float(np.mean([a == b for a, b in zip(y_true, y_pred)]))

    classes = sorted(set(y_true))
    precision: dict[str, float] = {}
    recall: dict[str, float] = {}
    f1: dict[str, float] = {}
    for cls in classes:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == cls and b == cls)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != cls and b == cls)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == cls and b != cls)
        precision[cls] = _safe_div(tp, tp + fp)
        recall[cls] = _safe_div(tp, tp + fn)
        denom = precision[cls] + recall[cls]
        f1[cls] = _safe_div(2 * precision[cls] * recall[cls], denom)

    # Balanced accuracy averages recall across classes; it is the fair
    # comparison when one direction dominates the sample.
    balanced_accuracy = float(np.mean([recall[c] for c in classes])) if classes else 0.0

    majority = max(set(y_true), key=y_true.count)
    baseline = float(np.mean([a == majority for a in y_true]))

    return {
        "horizon_days": horizon,
        "n_samples": len(y_true),
        "classes": classes,
        "majority_class": majority,
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "baseline_accuracy": baseline,
        "beats_baseline": bool(accuracy > baseline),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def summarize_metrics(metrics: dict) -> str:
    if not metrics.get("n_samples"):
        return metrics.get("error") or "No backtest results."
    lines = [
        f"Samples : {metrics['n_samples']}  (horizon={metrics['horizon_days']})",
        (
            f"Accuracy: {metrics['accuracy']:.3f}  "
            f"(baseline={metrics['baseline_accuracy']:.3f}, "
            f"balanced={metrics.get('balanced_accuracy', 0.0):.3f})"
        ),
        f"Majority: {metrics['majority_class']}",
        "",
        "Per-class F1:",
    ]
    for cls in metrics["classes"]:
        lines.append(
            f"  {cls:5s} P={metrics['precision'][cls]:.3f} "
            f"R={metrics['recall'][cls]:.3f} F1={metrics['f1'][cls]:.3f}"
        )
    return "\n".join(lines)


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def _empty_metrics(error: str = "No labelled rows available") -> dict:
    return {
        "n_samples": 0,
        "error": error,
        "classes": [],
        "majority_class": None,
        "accuracy": 0.0,
        "balanced_accuracy": 0.0,
        "baseline_accuracy": 0.0,
        "beats_baseline": False,
        "precision": {},
        "recall": {},
        "f1": {},
        "model_name": None,
        "folds": 0,
        "n_features": 0,
    }
