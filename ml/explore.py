"""Interactive model-lab orchestration.

``explore`` runs a full experiment for one ticker from a set of user-tunable
"knobs" (model family, horizon, label margin, feature groups, backtest folds),
fitting a fresh model and a walk-forward backtest on the supplied price history.
Everything is pure scikit-learn/numpy -- no LLM calls.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from . import backtest as backtest_mod
from . import config, dataset, features, labels, model
from .features import FEATURE_GROUPS, resolve_feature_columns

# Bounds enforced server-side so the lab cannot request unbounded work.
HORIZON_MIN, HORIZON_MAX = 1, 60
MARGIN_MIN, MARGIN_MAX = 0.0, 0.10
FOLDS_MIN, FOLDS_MAX = 2, 10
MAX_TRAIN_MIN, MAX_TRAIN_MAX = 60, 2000


def _clamp(value, low, high, default):
    try:
        if value is None:
            return default
        return max(low, min(high, value))
    except (TypeError, ValueError):
        return default


def available_models() -> list[dict]:
    """Return selectable model families for the UI."""
    return [
        {
            "name": name,
            "label": spec["label"],
            "description": spec["description"],
        }
        for name, spec in model.MODEL_SPECS.items()
    ]


def available_feature_groups() -> list[dict]:
    """Return selectable feature families with their column counts."""
    return [
        {"name": name, "columns": cols, "count": len(cols)}
        for name, cols in FEATURE_GROUPS.items()
    ]


def default_knobs() -> dict:
    return {
        "model_name": model.DEFAULT_MODEL,
        "horizon": config.HORIZON_DAYS,
        "margin": config.MARGIN,
        "feature_groups": list(FEATURE_GROUPS.keys()),
        "folds": config.BACKTEST_FOLDS,
        "max_train": config.BACKTEST_MAX_TRAIN,
    }


def normalize_knobs(raw: dict | None) -> dict:
    raw = raw or {}
    models = {name for name, _ in model.MODEL_SPECS.items()}
    model_name = raw.get("model_name")
    if model_name not in models:
        model_name = model.DEFAULT_MODEL

    groups = raw.get("feature_groups")
    if isinstance(groups, str):
        groups = [g for g in groups.split(",") if g]
    if not isinstance(groups, list) or not groups:
        groups = list(FEATURE_GROUPS.keys())
    groups = [g for g in groups if g in FEATURE_GROUPS] or list(FEATURE_GROUPS.keys())

    return {
        "model_name": model_name,
        "horizon": _clamp(
            raw.get("horizon"), HORIZON_MIN, HORIZON_MAX, config.HORIZON_DAYS
        ),
        "margin": _clamp(raw.get("margin"), MARGIN_MIN, MARGIN_MAX, config.MARGIN),
        "feature_groups": groups,
        "folds": _clamp(raw.get("folds"), FOLDS_MIN, FOLDS_MAX, config.BACKTEST_FOLDS),
        "max_train": _clamp(
            raw.get("max_train"),
            MAX_TRAIN_MIN,
            MAX_TRAIN_MAX,
            config.BACKTEST_MAX_TRAIN,
        ),
    }


def explore(price_payload, knobs: dict | None = None) -> dict:
    """Run a full prediction + backtest experiment for one ticker.

    ``price_payload`` may be a price-history payload accepted by
    :func:`ml.dataset.payload_to_frame` or an already-normalized DataFrame.
    """
    knobs = normalize_knobs(knobs)
    if isinstance(price_payload, pd.DataFrame):
        frame_raw = price_payload
    else:
        frame_raw = dataset.payload_to_frame(price_payload)
    if frame_raw is None or len(frame_raw) < config.MIN_HISTORY:
        raise ValueError(
            f"Insufficient history: need at least {config.MIN_HISTORY} rows"
        )

    feature_cols = resolve_feature_columns(knobs["feature_groups"])

    # One labelled frame shared by training and backtesting.
    labelled = labels.build_labelled_frame(
        frame_raw,
        horizon=knobs["horizon"],
        margin=knobs["margin"],
        feature_columns=knobs["feature_groups"],
    )
    if labelled.empty:
        raise ValueError("No labelled rows available for the chosen settings")

    predictor = model.train_on_frame(
        labelled,
        horizon=knobs["horizon"],
        model_name=knobs["model_name"],
        feature_columns=feature_cols,
        meta={"margin": knobs["margin"], "feature_groups": knobs["feature_groups"]},
    )

    # Live prediction from the latest available feature row.
    latest_features = features.compute_indicators(frame_raw)
    if latest_features.empty:
        raise ValueError("Insufficient history for a live feature vector")
    vector_frame = latest_features[feature_cols].iloc[[-1]]
    probs = predictor.predict_proba(vector_frame)
    direction = predictor.predict_direction(vector_frame)
    low = {k.lower(): v for k, v in probs.items()}

    metrics = backtest_mod.run_backtest(
        labelled,
        horizon=knobs["horizon"],
        folds=knobs["folds"],
        model_name=knobs["model_name"],
        feature_columns=feature_cols,
        max_train=knobs["max_train"],
    )

    # Class balance gives the user a feel for how the label scheme behaves.
    counts = labelled["target"].value_counts().to_dict()

    return {
        "direction": direction,
        "probability": round(max(probs.values()), 4),
        "prob_up": round(low.get("up", 0.0), 4),
        "prob_flat": round(low.get("flat", 0.0), 4),
        "prob_down": round(low.get("down", 0.0), 4),
        "confidence": predictor.confidence(
            low.get("up", 0.0), low.get("down", 0.0), low.get("flat", 0.0)
        ),
        "model_name": predictor.meta.get("model_name"),
        "model_version": predictor.version,
        "trained_on": predictor.meta.get("trained_on"),
        "horizon_days": knobs["horizon"],
        "margin": knobs["margin"],
        "feature_groups": knobs["feature_groups"],
        "feature_columns": feature_cols,
        "n_features": len(feature_cols),
        "n_samples": int(labelled.shape[0]),
        "class_balance": {str(k): int(v) for k, v in counts.items()},
        "features": model.Predictor.feature_importance(predictor, top_n=8),
        "backtest": metrics,
        "knobs": knobs,
        "generated_at": datetime.now(UTC).isoformat(),
    }
