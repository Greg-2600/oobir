# Machine Learning Predictions

This document is a deep dive into OOBIR's machine-learning price-direction
feature: the `ml/` package, the REST endpoints, the interactive **AI Predictions
Lab**, and the design decisions behind them.

> **Design principle:** the ML layer is pure `scikit-learn` + `numpy`/`pandas`.
> No LLM or Ollama call ever happens in the ML request path. The LLM layer
> (`flow.py`) is a separate, optional consumer of ML output.

---

## 1. What it predicts

For a ticker and a horizon `h` (trading days), the model predicts the direction
of the forward return:

```
forward_return(t) = Close[t + h] / Close[t] - 1
```

- `forward_return > margin` → **UP**
- `forward_return < -margin` → **DOWN**
- otherwise → **FLAT** (only when `margin > 0`)

The default `margin` is `0.0`, which makes this a clean binary up/down call.
Raising `margin` introduces a FLAT dead-band around zero.

---

## 2. Package layout

```
ml/
├── __init__.py      # package exports
├── config.py        # env-overridable defaults (OOOBIR_ML_*)
├── features.py      # feature engineering + feature groups
├── labels.py        # forward-return labeling
├── dataset.py       # price-payload parsing + dataset assembly
├── model.py         # estimator families, persistence, inference
├── backtest.py      # walk-forward validation and metrics
├── explore.py       # interactive-lab orchestration + knob clamping
├── train.py         # CLI (train / predict / backtest)
└── __main__.py      # enables `python -m ml ...`
```

---

## 3. Features

`ml/features.py` computes **17 trailing features**. Every window ends at row
`t`, so a feature at time `t` never depends on future data. Warm-up rows
containing `NaN` are dropped, so a minimum of ~50 rows of history is required
before any feature is usable.

| Feature | Description |
|---------|-------------|
| `ret_1`, `ret_5`, `ret_10` | Close-to-close returns over 1/5/10 days |
| `log_ret_1` | 1-day log return |
| `volatility_10`, `volatility_20` | Rolling std of log returns |
| `return_std_10` | Rolling std of 1-day returns |
| `volume_zscore_20` | Volume relative to its 20-day mean |
| `SMA_20`, `SMA_50` | Simple moving averages |
| `close_sma20_gap`, `close_sma50_gap` | Relative close-to-SMA gaps |
| `RSI_14` | Wilder RSI |
| `BB_percent_b` | Bollinger %B |
| `MACD`, `MACD_Signal`, `MACD_hist` | MACD line, signal, histogram |

### Feature groups

Features are grouped so the lab can toggle whole signal families:

| Group | Count | Members |
|-------|-------|---------|
| `returns` | 4 | `ret_1`, `ret_5`, `ret_10`, `log_ret_1` |
| `volatility` | 3 | `volatility_10`, `volatility_20`, `return_std_10` |
| `volume` | 1 | `volume_zscore_20` |
| `trend` | 4 | `SMA_20`, `SMA_50`, `close_sma20_gap`, `close_sma50_gap` |
| `rsi` | 1 | `RSI_14` |
| `bollinger` | 1 | `BB_percent_b` |
| `macd` | 3 | `MACD`, `MACD_Signal`, `MACD_hist` |

`resolve_feature_columns(groups)` returns the selected columns in canonical
order, de-duplicated. An empty selection resolves to all features.

---

## 4. Models

`ml/model.py` exposes a `MODEL_SPECS` registry. Each entry has a human label, a
description, and an estimator factory:

| Key | Estimator | Notes |
|-----|-----------|-------|
| `hist_gbm` | `HistGradientBoostingClassifier` | Default workhorse; native missing-value handling |
| `random_forest` | `RandomForestClassifier` | Bagged trees; robust, slower |
| `extra_trees` | `ExtraTreesClassifier` | Randomized splits; fast, high-variance |
| `logistic` | `LogisticRegression` (scaled pipeline) | Linear baseline |

All tree models use `class_weight="balanced"` and a fixed `random_state=42` for
reproducibility. A lightweight `fast_estimator()` (fewer boosting iterations) is
used for walk-forward backtest folds to keep them responsive.

### Persistence

`Predictor` bundles the fitted estimator, the ordered feature names, the class
list, and metadata. `save()` writes a `.joblib` artifact plus `meta.json` under
`models/` (gitignored). Metadata includes the model version, model name,
horizon, margin, feature list, training timestamp, row count, and permutation
importances.

### Explainability

`HistGradientBoostingClassifier` does not expose `feature_importances_`, so
importances are computed with `sklearn.inspection.permutation_importance` at
training time and stored in metadata. `Predictor.feature_importance()` reads
them back (with a fallback to built-in importances for estimators that have
them).

---

## 5. Walk-forward backtesting

`ml/backtest.py` uses an **expanding-train / rolling-test** split ordered by
`Date`:

1. Train on the first `min_train` rows.
2. Predict the next `step` rows.
3. Roll forward and repeat for `folds` iterations.

Metrics reported:
- `accuracy`, `balanced_accuracy`, `baseline_accuracy` (majority class)
- `beats_baseline` (accuracy > baseline)
- per-class `precision`, `recall`, `f1`
- `n_samples`, `classes`, `majority_class`, `folds`, `n_features`

`max_train` caps each fold's training window so backtests stay fast on long
series. Honest reality: short-horizon directional accuracy is usually close to
the majority baseline. The API surfaces `balanced_accuracy` and
`beats_baseline` so consumers can judge the model rather than trusting headline
accuracy.

---

## 6. Interactive lab orchestration

`ml/explore.py` is the entry point used by the `/explore` endpoint. It:

1. Normalizes and clamps every knob server-side.
2. Builds one labelled frame shared by training and backtesting.
3. Trains a fresh model for the requested configuration.
4. Predicts from the latest feature row.
5. Runs a walk-forward backtest.
6. Returns the prediction, feature drivers, class balance, and metrics.

### Knob bounds

| Knob | Param | Min | Max | Default |
|------|-------|-----|-----|---------|
| Model | `model_name` | — | — | `hist_gbm` |
| Horizon | `horizon` | 1 | 60 | `5` |
| Margin | `margin` | 0.0 | 0.10 | `0.0` |
| Folds | `folds` | 2 | 10 | `3` |
| Train cap | `max_train` | 60 | 2000 | `200` |

Unknown model names fall back to the default; empty feature-group selections
resolve to all groups.

---

## 7. API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/ml/options` | Models, feature groups, defaults, and bounds |
| `GET` | `/api/predict/{symbol}?horizon=5` | Cached-model directional forecast |
| `GET` | `/api/predict/{symbol}/backtest?horizon=5` | Cached walk-forward backtest |
| `GET` | `/api/predict/{symbol}/features?top_n=5` | Cached-model feature importances |
| `GET` | `/api/predict/{symbol}/explore` | Full lab experiment from knobs |

### Example: explore request

```bash
curl "http://localhost:2010/api/predict/AAPL/explore?model_name=random_forest&horizon=20&margin=0.02&feature_groups=returns,volatility,trend,macd&folds=5&max_train=300"
```

Example response (abridged):

```json
{
  "symbol": "AAPL",
  "direction": "DOWN",
  "probability": 0.58,
  "prob_up": 0.42,
  "prob_flat": 0.0,
  "prob_down": 0.58,
  "confidence": "MEDIUM",
  "model_name": "random_forest",
  "horizon_days": 20,
  "margin": 0.02,
  "n_features": 14,
  "n_samples": 1931,
  "class_balance": {"UP": 1142, "DOWN": 535, "FLAT": 254},
  "features": [{"feature": "volatility_20", "importance": 0.13}, "..."],
  "backtest": {"accuracy": 0.34, "baseline_accuracy": 0.58, "folds": 5, "...": "..."},
  "knobs": {"model_name": "random_forest", "horizon": 20, "...": "..."},
  "cached": false
}
```

### Status codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `422` | Insufficient history (< `OOOBIR_ML_MIN_HISTORY` rows) or no labelled rows |
| `503` | Cached model not trained (only for `/predict`, `/backtest`, `/features`) |
| `500` | Unexpected error |

---

## 8. CLI

```bash
python -m ml train --universe sp500 --save       # train + persist + backtest
python -m ml train --size 20 --live --save        # fetch missing tickers via yfinance
python -m ml predict --ticker AAPL                # predict from stored history
python -m ml backtest --ticker AAPL               # walk-forward metrics
```

---

## 9. Performance engineering

- **Date-bounded history queries.** TimescaleDB's `price_history` hypertable has
  thousands of chunks. Passing a concrete cutoff timestamp (rather than
  `make_interval`) lets the planner prune chunks, cutting planning time from
  multiple seconds to sub-second.
- **Long-window ML history.** ML endpoints fetch a multi-year window instead of
  the 121-day UI trim, so backtests have enough samples.
- **Training-window caps.** `max_train` keeps each backtest fold cheap.
- **In-process explore cache.** Identical `(symbol, model, horizon, margin,
  feature_groups, folds, max_train)` configurations are cached in a bounded
  FIFO, making repeated runs and preset toggles near-instant.

---

## 10. Configuration

All settings are environment-overridable via the `OOOBIR_ML_*` prefix (see
`ml/config.py`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `OOOBIR_ML_HORIZON` | `5` | Default forecast horizon (days) |
| `OOOBIR_ML_MARGIN` | `0.0` | FLAT dead-band |
| `OOOBIR_ML_WINDOW` | `250` | Trailing feature window |
| `OOOBIR_ML_MIN_HISTORY` | `120` | Minimum rows for a prediction |
| `OOOBIR_ML_MODEL_DIR` | `models/` | Artifact directory |
| `OOOBIR_ML_BT_FOLDS` | `3` | Default walk-forward folds |
| `OOOBIR_ML_BT_MAX_TRAIN` | `200` | Fold training-window cap |
| `OOOBIR_ML_ENABLE` | off | Master switch for broader ML surfacing |

---

## 11. Testing

`tests/test_ml.py` covers:

- Feature matrix shape and no-look-ahead leakage checks
- Forward-return labeling (including FLAT bands)
- Train/predict/feature-importance round trips
- Walk-forward backtest metrics
- Feature-group resolution and subsetting
- Explore orchestration across all four model families
- Knob clamping
- REST endpoints (`/api/ml/options`, `/api/predict/.../explore`) via `TestClient`
- Static UI contracts for the AI Predictions page

Run them with:

```bash
pytest tests/test_ml.py -v
```

---

## 12. Limitations & roadmap

- Short-horizon direction is a hard, near-random problem; expect accuracy close
  to the majority baseline. Treat the signal as advisory.
- The model is trained per-request in the lab; the persisted model is a single
  global artifact. Per-ticker models and periodic retraining are natural next
  steps.
- Candidate upgrades: gradient boosting (`XGBoost`/`LightGBM`), sequence models
  (LSTM/GRU), richer features (cross-asset, macro), and probability calibration.
