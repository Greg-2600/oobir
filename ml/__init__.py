"""Machine-learning price-direction prediction module for OOBIR.

Pure scikit-learn models -- no LLM/Ollama calls at request time. Exposed to the
REST API via flow_api.py and consumed by the interactive AI Predictions lab
(web/predictions.html).
"""

from . import backtest, config, dataset, explore, features, labels, model

__all__ = [
    "backtest",
    "config",
    "dataset",
    "explore",
    "features",
    "labels",
    "model",
]
