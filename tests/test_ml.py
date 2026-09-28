"""Tests for the ML prediction module and its REST endpoints."""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

# Ensure project root is on path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import flow_api
from ml import backtest, explore, features, labels, model


def _sample_price_df(days: int = 200, uptrend: bool = True) -> pd.DataFrame:
    """Synthetic OHLCV frame with a clean directional trend + noise."""
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    dates = [base + timedelta(days=i) for i in range(days)]
    drift = 0.5 if uptrend else -0.5
    rng = np.random.default_rng(0)
    noise = rng.normal(0, 0.6, days)
    close = [100 + drift * i + noise[i] for i in range(days)]
    open_ = [c - 0.3 for c in close]
    high = [c + 0.8 for c in close]
    low = [c - 0.8 for c in close]

    base_vol = 1_000_000
    vol_noise = rng.integers(0, 200_000, days)
    volume = [base_vol + int(v) for v in vol_noise]

    return pd.DataFrame(
        {
            "Date": dates,
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }
    )


class TestFeatures(unittest.TestCase):
    def test_compute_indicators_column_shape(self):
        df = _sample_price_df(200)
        ind = features.compute_indicators(df)
        self.assertFalse(ind.empty)
        self.assertEqual(list(ind.columns), features.FEATURE_COLUMNS)
        self.assertTrue(ind.notna().all().all(), "No NaN after warm-up")

    def test_no_lookahead_leakage(self):
        # Feature at index i must not depend on Close[i] forward info. We verify
        # shifting a trailing window by one row only differs by the warm-up.
        df = _sample_price_df(200)
        ind = features.compute_indicators(df)
        # ret_5 at row i uses Close[i-5..i]; the first 5 rows of the frame are
        # the warm-up. Recomputing on a truncated frame aligned to the same
        # rows should be identical once warm-up is dropped.
        truncated = df.iloc[:-5].reset_index(drop=True)
        ind_trunc = features.compute_indicators(truncated)
        # The last row of `ind_trunc` uses only data up to that point; the same
        # row in the full frame must match.
        self.assertTrue(np.allclose(ind.iloc[-6], ind_trunc.iloc[-1], equal_nan=True))

    def test_insufficient_history_returns_empty(self):
        df = _sample_price_df(30)
        ind = features.compute_indicators(df)
        self.assertTrue(ind.empty)


class TestLabels(unittest.TestCase):
    def test_label_upward_trend_is_up(self):
        df = _sample_price_df(200, uptrend=True)
        frame = labels.build_labelled_frame(df, horizon=5)
        self.assertFalse(frame.empty)
        self.assertIn("target", frame.columns)
        # A steady strong uptrend should be predominantly UP.
        self.assertGreater((frame["target"] == "UP").mean(), 0.5)


class TestModelInference(unittest.TestCase):
    def _frame(self):
        frames = [
            labels.build_labelled_frame(_sample_price_df(200, up), 5)
            for up in (True, False)
        ]
        return pd.concat(frames, ignore_index=True)

    def test_train_and_predict_proba(self):
        frame = self._frame()
        with tempfile.TemporaryDirectory() as tmp:
            predictor = model.train_on_frame(frame, horizon=5, meta={"__fake": True})
            path = predictor.save(tmp + "/model.joblib")
            loaded = model.Predictor.load(path)
            vector, _ = features.make_feature_vector(_sample_price_df(200, True))
            probs = loaded.predict_proba(vector)
            self.assertTrue(set(probs).issubset({"UP", "FLAT", "DOWN"}))
            self.assertTrue(set(probs))
            self.assertAlmostEqual(sum(probs.values()), 1.0, places=5)
            direction = loaded.predict_direction(vector)
            self.assertIn(direction, loaded.classes)
            self.assertIsInstance(loaded.confidence(0.8, 0.1, 0.1), str)

    def test_feature_importance(self):
        frame = self._frame()
        predictor = model.train_on_frame(frame, horizon=5)
        tops = model.Predictor.feature_importance(predictor, top_n=3)
        self.assertLessEqual(len(tops), 3)
        for item in tops:
            self.assertIn(item["feature"], features.FEATURE_COLUMNS)


class TestBacktest(unittest.TestCase):
    def test_walk_forward_returns_metrics(self):
        df = pd.concat(
            [
                labels.build_labelled_frame(_sample_price_df(200, up), 5)
                for up in (True, False)
            ],
            ignore_index=True,
        )
        metrics = backtest.run_backtest(df, horizon=5, folds=3)
        self.assertGreater(metrics["n_samples"], 0)
        self.assertIn("accuracy", metrics)
        self.assertIn("baseline_accuracy", metrics)
        self.assertIn("balanced_accuracy", metrics)
        self.assertIn("beats_baseline", metrics)
        self.assertGreaterEqual(metrics["accuracy"], 0.0)
        self.assertLessEqual(metrics["accuracy"], 1.0)

    def test_empty_frame_safe(self):
        metrics = backtest.run_backtest(pd.DataFrame())
        self.assertEqual(metrics["n_samples"], 0)
        self.assertIn("error", metrics)


class TestPredictEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(flow_api.app)
        self.symbol = "TESTML"

    def _history_payload(self):
        df = _sample_price_df(200, uptrend=True)
        df["Date"] = df["Date"].astype(str)
        return {"data": df.to_dict(orient="records")}

    @patch("flow_api.get_ml_price_history_payload")
    @patch("ml.model.Predictor.load")
    def test_predict_returns_shape(self, mock_load, mock_history):
        mock_history.return_value = self._history_payload()
        predictor = model.train_on_frame(
            pd.concat(
                [
                    labels.build_labelled_frame(_sample_price_df(200, up), 5)
                    for up in (True, False)
                ],
                ignore_index=True,
            ),
            horizon=5,
        )
        mock_load.return_value = predictor

        resp = self.client.get(f"/api/predict/{self.symbol}?horizon=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("direction", data)
        self.assertIn("prob_up", data)
        self.assertIn("prob_flat", data)
        self.assertIn("prob_down", data)
        self.assertAlmostEqual(
            data["prob_up"] + data["prob_flat"] + data["prob_down"], 1.0, places=2
        )

    @patch("flow_api.get_ml_price_history_payload")
    @patch("ml.model.Predictor.load")
    def test_untrained_model_returns_503(self, mock_load, mock_history):
        mock_history.return_value = self._history_payload()
        mock_load.side_effect = FileNotFoundError("no model")

        resp = self.client.get(f"/api/predict/{self.symbol}")
        self.assertEqual(resp.status_code, 503)

    @patch("flow_api.get_ml_price_history_payload")
    def test_insufficient_history_returns_422(self, mock_history):
        mock_history.return_value = {
            "data": _sample_price_df(30).to_dict(orient="records")
        }
        resp = self.client.get(f"/api/predict/{self.symbol}")
        self.assertEqual(resp.status_code, 422)

    @patch("flow_api.get_ml_price_history_payload")
    def test_backtest_endpoint(self, mock_history):
        mock_history.return_value = self._history_payload()
        resp = self.client.get(f"/api/predict/{self.symbol}/backtest?horizon=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("accuracy", data)
        self.assertEqual(data["symbol"].upper(), self.symbol)

    @patch("flow_api.get_ml_price_history_payload")
    @patch("ml.model.Predictor.load")
    def test_features_endpoint(self, mock_load, mock_history):
        mock_history.return_value = self._history_payload()
        frame = pd.concat(
            [
                labels.build_labelled_frame(_sample_price_df(200, up), 5)
                for up in (True, False)
            ],
            ignore_index=True,
        )
        mock_load.return_value = model.train_on_frame(frame, horizon=5)

        resp = self.client.get(f"/api/predict/{self.symbol}/features?top_n=3")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertLessEqual(len(data["features"]), 3)


class TestFeatureSelection(unittest.TestCase):
    def test_resolve_feature_columns_subset(self):
        cols = features.resolve_feature_columns(["returns", "rsi"])
        self.assertIn("ret_1", cols)
        self.assertIn("RSI_14", cols)
        self.assertNotIn("MACD", cols)

    def test_resolve_empty_returns_all(self):
        self.assertEqual(features.resolve_feature_columns([]), features.FEATURE_COLUMNS)

    def test_labelled_frame_honors_feature_subset(self):
        frame = labels.build_labelled_frame(
            _sample_price_df(200), horizon=5, feature_columns=["returns", "volume"]
        )
        feature_cols = [c for c in frame.columns if c not in ("target", "Date")]
        self.assertIn("ret_1", feature_cols)
        self.assertNotIn("MACD", feature_cols)

    def test_margin_creates_flat_class(self):
        frame = labels.build_labelled_frame(
            _sample_price_df(200), horizon=5, margin=0.05
        )
        self.assertIn("target", frame.columns)
        # A wide band should produce FLAT labels.
        self.assertIn("FLAT", set(frame["target"]))


class TestExplore(unittest.TestCase):
    def _frame(self):
        return _sample_price_df(250, uptrend=True)

    def test_explore_returns_full_shape(self):
        result = explore.explore(
            self._frame(),
            {
                "model_name": "hist_gbm",
                "horizon": 5,
                "margin": 0.0,
                "feature_groups": ["returns", "volatility"],
                "folds": 2,
                "max_train": 120,
            },
        )
        for key in (
            "direction",
            "prob_up",
            "prob_down",
            "prob_flat",
            "n_features",
            "n_samples",
            "backtest",
            "features",
            "class_balance",
            "knobs",
        ):
            self.assertIn(key, result)
        self.assertEqual(result["n_features"], 7)

    def test_explore_clamps_bad_knobs(self):
        knobs = explore.normalize_knobs(
            {"horizon": 9999, "margin": -5, "folds": 0, "model_name": "nope"}
        )
        self.assertEqual(knobs["horizon"], explore.HORIZON_MAX)
        self.assertEqual(knobs["margin"], explore.MARGIN_MIN)
        self.assertGreaterEqual(knobs["folds"], explore.FOLDS_MIN)
        self.assertEqual(knobs["model_name"], model.DEFAULT_MODEL)

    def test_all_model_families_fit(self):
        mixed = pd.concat(
            [_sample_price_df(150, up) for up in (True, False)], ignore_index=True
        )
        for name in model.MODEL_SPECS:
            result = explore.explore(
                mixed,
                {
                    "model_name": name,
                    "horizon": 5,
                    "feature_groups": ["returns", "trend"],
                    "folds": 2,
                    "max_train": 120,
                },
            )
            self.assertIn(result["direction"], {"UP", "DOWN", "FLAT"})


class TestMlOptionsEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(flow_api.app)

    def test_options_endpoint(self):
        resp = self.client.get("/api/ml/options")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        names = [m["name"] for m in data["models"]]
        self.assertIn("hist_gbm", names)
        self.assertIn("logistic", names)
        self.assertTrue(data["feature_groups"])
        self.assertIn("defaults", data)

    @patch("flow_api.get_ml_price_history_payload")
    def test_explore_endpoint(self, mock_history):
        df = _sample_price_df(250, uptrend=True)
        df["Date"] = df["Date"].astype(str)
        mock_history.return_value = {"data": df.to_dict(orient="records")}
        resp = self.client.get(
            "/api/predict/TESTML/explore?model_name=logistic&horizon=5"
            "&margin=0.01&feature_groups=returns,rsi&folds=2&max_train=120"
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["model_name"], "logistic")
        self.assertIn("backtest", data)
        self.assertEqual(data["symbol"], "TESTML")


class TestPredictionsPageContracts(unittest.TestCase):
    """Static checks for the interactive AI Predictions lab page."""

    def _page(self):
        path = Path(__file__).resolve().parent.parent / "web" / "predictions.html"
        return path.read_text(encoding="utf-8")

    def test_page_has_required_controls(self):
        html = self._page()
        self.assertIn('id="ml-ticker-input"', html)
        self.assertIn('id="ml-run-btn"', html)
        self.assertIn('id="lab-model"', html)
        self.assertIn('id="lab-horizon"', html)
        self.assertIn('id="lab-margin"', html)
        self.assertIn('id="lab-feature-chips"', html)
        self.assertIn('id="ml-chart"', html)

    def test_page_links_assets(self):
        html = self._page()
        self.assertIn("predictions.js", html)
        self.assertIn("config.js", html)

    def test_js_references_ml_endpoints(self):
        js_path = Path(__file__).resolve().parent.parent / "web" / "predictions.js"
        js = js_path.read_text(encoding="utf-8")
        self.assertIn("/api/predict/", js)
        self.assertIn("/api/price-history/", js)
        self.assertIn("renderChart", js)

    def test_nav_has_predictions_link_on_stock_pages(self):
        web = Path(__file__).resolve().parent.parent / "web"
        for name in ("index.html", "stocks.html", "search.html", "markets.html"):
            html = (web / name).read_text(encoding="utf-8")
            self.assertIn(
                'href="predictions.html"',
                html,
                f"{name} is missing the AI Predictions nav link",
            )


if __name__ == "__main__":
    unittest.main()
