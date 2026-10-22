"""Model persistence and inference.

A :class:`Predictor` bundles the fitted estimator plus the metadata needed to
interpret predictions (feature list, label classes, version). Predictions are
pure scikit-learn/numpy -- no network, no LLM, no Ollama.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import config, features

_LOCK = threading.Lock()

# Selectable estimator families for the interactive lab. Each entry is a
# factory plus a short human label and a "cost" hint used by the UI.
MODEL_SPECS = {
    "hist_gbm": {
        "label": "Hist Gradient Boosting",
        "description": "Fast, handles missing values; the default workhorse.",
        "factory": lambda: HistGradientBoostingClassifier(
            max_iter=300,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=42,
        ),
    },
    "random_forest": {
        "label": "Random Forest",
        "description": "Bagged decision trees; robust but slower to fit.",
        "factory": lambda: RandomForestClassifier(
            n_estimators=120,
            max_depth=10,
            min_samples_leaf=25,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42,
        ),
    },
    "extra_trees": {
        "label": "Extra Trees",
        "description": "Randomized splits; fast and high-variance.",
        "factory": lambda: ExtraTreesClassifier(
            n_estimators=120,
            max_depth=10,
            min_samples_leaf=25,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42,
        ),
    },
    "logistic": {
        "label": "Logistic Regression",
        "description": "Linear baseline with feature scaling.",
        "factory": lambda: Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        ),
    },
}

DEFAULT_MODEL = "hist_gbm"


def normalize_model_name(name: str | None) -> str:
    if name in MODEL_SPECS:
        return name
    return DEFAULT_MODEL


def estimator_factory(name: str | None = None):
    """Return the estimator factory for a model name (falls back to default)."""
    return MODEL_SPECS[normalize_model_name(name)]["factory"]


def build_estimator(name: str | None = None):
    """Construct a fresh estimator for the given model name."""
    return estimator_factory(name)()


def default_model_path() -> str:
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    return os.path.join(config.MODEL_DIR, "model.joblib")


def metadata_path() -> str:
    return os.path.join(config.MODEL_DIR, "meta.json")


def default_estimator() -> HistGradientBoostingClassifier:
    return build_estimator(DEFAULT_MODEL)


def fast_estimator() -> HistGradientBoostingClassifier:
    """Lighter estimator for walk-forward backtests.

    Refitting across folds is the expensive part of a backtest; fewer boosting
    iterations keep the endpoint responsive while preserving the same feature
    matrix and label scheme.
    """
    return HistGradientBoostingClassifier(
        max_iter=80,
        learning_rate=0.1,
        max_leaf_nodes=15,
        min_samples_leaf=30,
        class_weight="balanced",
        random_state=42,
    )


class Predictor:
    """Thin wrapper around a fitted estimator plus metadata."""

    def __init__(self, estimator, feature_names, classes, meta=None):
        self.estimator = estimator
        # Keep a canonical ordered class list.
        self.classes = list(classes)
        self.feature_names = list(feature_names)
        self.meta = meta or {}

    @property
    def version(self) -> str:
        return self.meta.get("model_version") or config.MODEL_VERSION

    @property
    def trained_on(self) -> str | None:
        return self.meta.get("trained_on")

    def _as_frame(self, feature_vector):
        """Wrap a feature vector as a named DataFrame to avoid sklearn warnings."""
        if isinstance(feature_vector, pd.DataFrame):
            return feature_vector
        return pd.DataFrame([feature_vector], columns=self.feature_names)

    def predict_proba(self, feature_vector: list[float]) -> dict[str, float]:
        """Return {DIRECTION: probability} for a feature vector."""
        if not isinstance(feature_vector, pd.DataFrame) and len(feature_vector) != len(
            self.feature_names
        ):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, got "
                f"{len(feature_vector)}"
            )
        x = self._as_frame(feature_vector)
        probs = self.estimator.predict_proba(x)[0]
        return {cls: float(prob) for cls, prob in zip(self.classes, probs)}

    def predict_direction(self, feature_vector: list[float]) -> str:
        return self.estimator.predict(self._as_frame(feature_vector))[0]

    @staticmethod
    def confidence(prob_up: float, prob_down: float, prob_flat: float) -> str:
        peak = max(prob_up, prob_down, prob_flat)
        # Normalize confidence to the winning class share.
        total = prob_up + prob_down + prob_flat
        if total <= 0:
            return "LOW"
        share = peak / total
        if share >= 0.6:
            return "HIGH"
        if share >= 0.5:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def feature_importance(predictor: Predictor, top_n: int = 5) -> list[dict]:
        """Return the top contributing features of the boosted model.

        Histogram gradient boosting does not expose ``feature_importances_``,
        so importances are computed with permutation importance at training
        time and stored in the model metadata.
        """
        stored = predictor.meta.get("feature_importances")
        if stored:
            return stored[:top_n]

        # Fallback: any estimator that does expose built-in importances.
        estimator = predictor.estimator
        attr = getattr(estimator, "feature_importances_", None)
        if attr is None:
            return []
        order = np.argsort(attr)[::-1][:top_n]
        return [
            {"feature": predictor.feature_names[i], "importance": float(attr[i])}
            for i in order
        ]

    def save(self, path: str | None = None) -> str:
        path = path or default_model_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        artifact = {
            "estimator": self.estimator,
            "feature_names": self.feature_names,
            "classes": self.classes,
            "meta": self.meta,
        }
        joblib.dump(artifact, path)
        with open(metadata_path(), "w", encoding="utf-8") as fh:
            json.dump(self.meta, fh, indent=2)
        return path

    @staticmethod
    def load(path: str | None = None) -> Predictor:
        path = path or default_model_path()
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"No trained model at {path}. Run `python -m ml train`."
            )
        artifact = joblib.load(path)
        return Predictor(
            estimator=artifact["estimator"],
            feature_names=artifact["feature_names"],
            classes=artifact["classes"],
            meta=artifact.get("meta", {}),
        )


def train_on_frame(
    frame,
    horizon: int | None = None,
    meta=None,
    model_name: str | None = None,
    feature_columns: list[str] | None = None,
) -> Predictor:
    """Fit and return a :class:`Predictor` from a labelled feature frame."""
    feature_cols = [
        c for c in (feature_columns or features.FEATURE_COLUMNS) if c in frame.columns
    ]
    if not feature_cols:
        feature_cols = [c for c in features.FEATURE_COLUMNS if c in frame.columns]
    X = frame[feature_cols]
    y = frame["target"].astype(str)

    estimator = build_estimator(model_name)
    estimator.fit(X, y)

    resolved_meta = dict(meta or {})
    resolved_meta.setdefault("model_version", config.MODEL_VERSION)
    resolved_meta.setdefault("model_name", normalize_model_name(model_name))
    resolved_meta.setdefault(
        "horizon_days", horizon if horizon is not None else config.HORIZON_DAYS
    )
    resolved_meta.setdefault("margin", config.MARGIN)
    resolved_meta.setdefault("feature_columns", list(feature_cols))
    resolved_meta.setdefault("trained_on", datetime.now(UTC).isoformat())
    resolved_meta.setdefault("rows", int(frame.shape[0]))
    if "feature_importances" not in resolved_meta:
        resolved_meta["feature_importances"] = _permutation_importances(
            estimator, X, y, feature_cols
        )

    return Predictor(estimator, feature_cols, sorted(set(y)), resolved_meta)


def _permutation_importances(estimator, X, y, feature_cols, top_n: int = 8):
    """Compute permutation importances, degrading gracefully on any error."""
    try:
        from sklearn.inspection import permutation_importance

        sample = X
        sample_y = y
        if len(X) > 1000:
            idx = np.linspace(0, len(X) - 1, 1000).astype(int)
            sample = X.iloc[idx]
            sample_y = y.iloc[idx]
        result = permutation_importance(
            estimator, sample, sample_y, n_repeats=3, random_state=42, n_jobs=-1
        )
        means = result.importances_mean
        order = np.argsort(means)[::-1][:top_n]
        return [
            {"feature": feature_cols[i], "importance": float(max(means[i], 0.0))}
            for i in order
        ]
    except Exception:  # pylint: disable=broad-except
        return []
