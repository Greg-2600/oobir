"""Runtime configuration for the ML prediction models.

All values can be overridden through environment variables, mirroring the
OOOBIR_ML_ prefix convention used elsewhere in the project.
"""

import os


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# Forecast horizon in trading days (label = sign of forward return over this).
HORIZON_DAYS = _env_int("OOOBIR_ML_HORIZON", 5)

# Symmetric margin around zero-return; returns within +/-MARGIN are "FLAT".
# Empirically, a nonzero band adds label noise that hurts walk-forward
# accuracy, so the default is 0 (effectively a directional up/down call).
MARGIN = _env_float("OOOBIR_ML_MARGIN", 0.0)

# Number of trailing trading days used to build each feature vector.
WINDOW = _env_int("OOOBIR_ML_WINDOW", 250)

# Minimum number of history rows required to build a usable prediction window.
MIN_HISTORY = _env_int("OOOBIR_ML_MIN_HISTORY", 120)

# Directory where serialized model artifacts live.
MODEL_DIR = os.getenv("OOOBIR_ML_MODEL_DIR", os.path.join(os.getcwd(), "models"))

# Optional master switch for surfacing ML output beyond the dedicated lab page.
ENABLE = os.getenv("OOOBIR_ML_ENABLE", "0") == "1"

# Backtest walk-forward parameters.
BACKTEST_MIN_TRAIN = _env_int("OOOBIR_ML_BT_MIN_TRAIN", 60)
BACKTEST_FOLDS = _env_int("OOOBIR_ML_BT_FOLDS", 3)
# Cap each fold's training window so backtests stay responsive on long series.
# Empirically keeps a single-symbol backtest well under a second.
BACKTEST_MAX_TRAIN = _env_int("OOOBIR_ML_BT_MAX_TRAIN", 200)

# Model identity. Bump when the feature set or label scheme changes.
MODEL_VERSION = "1.0.0"

DIRECTIONS = ("UP", "FLAT", "DOWN")
