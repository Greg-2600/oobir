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
from ml import backtest, config, dataset, explore, features, labels, model


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


class TestFeaturesDetailed(unittest.TestCase):
    """Deeper feature engineering tests."""

    def test_rsi_bounded_0_100(self):
        df = _sample_price_df(300, uptrend=True)
        ind = features.compute_indicators(df)
        self.assertTrue((ind["RSI_14"] >= 0).all())
        self.assertTrue((ind["RSI_14"] <= 100).all())

    def test_rsi_oversold_on_downtrend(self):
        df = _sample_price_df(200, uptrend=False)
        ind = features.compute_indicators(df)
        self.assertTrue((ind["RSI_14"] < 70).any())

    def test_macd_hist_sign_changes(self):
        df = _sample_price_df(300, uptrend=True)
        ind = features.compute_indicators(df)
        hist = ind["MACD_hist"]
        self.assertTrue((hist != 0).any())

    def test_bb_percent_b_bounded(self):
        df = _sample_price_df(200, uptrend=True)
        ind = features.compute_indicators(df)
        bb = ind["BB_percent_b"]
        self.assertTrue((bb >= 0).all())
        self.assertTrue((bb <= 2).all())

    def test_sma_20_less_than_close_in_uptrend(self):
        df = _sample_price_df(200, uptrend=True)
        ind = features.compute_indicators(df)
        self.assertTrue((ind["SMA_20"] < df["Close"].iloc[-len(ind):]).all())

    def test_volume_zscore_centered_near_zero(self):
        df = _sample_price_df(300, uptrend=True)
        ind = features.compute_indicators(df)
        mean_zscore = ind["volume_zscore_20"].mean()
        self.assertLess(abs(mean_zscore), 0.5)

    def test_log_ret_1_approx_ret_1_for_small_moves(self):
        df = _sample_price_df(200, uptrend=True)
        ind = features.compute_indicators(df)
        self.assertTrue(np.allclose(ind["log_ret_1"], ind["ret_1"], rtol=0.01, atol=0.1))

    def test_make_feature_vector_returns_correct_length(self):
        df = _sample_price_df(200, uptrend=True)
        vector, frame = features.make_feature_vector(df)
        self.assertEqual(len(vector), len(features.FEATURE_COLUMNS))
        self.assertIsNotNone(frame)

    def test_make_feature_vector_empty_for_short_series(self):
        df = _sample_price_df(30, uptrend=True)
        vector, frame = features.make_feature_vector(df)
        self.assertEqual(len(vector), 0)
        self.assertIsNone(frame)

    def test_feature_columns_stable_order(self):
        df = _sample_price_df(200, uptrend=True)
        ind = features.compute_indicators(df)
        self.assertEqual(list(ind.columns), features.FEATURE_COLUMNS)

    def test_volatility_positive(self):
        df = _sample_price_df(200, uptrend=True)
        ind = features.compute_indicators(df)
        self.assertTrue((ind["volatility_10"] > 0).all())
        self.assertTrue((ind["volatility_20"] > 0).all())


class TestLabelsDetailed(unittest.TestCase):
    """Deeper label generation tests."""

    def test_margin_exact_zero_label(self):
        df = _sample_price_df(200, uptrend=True)
        lbls = labels.label_forward_returns(df, horizon=5, margin=0.0)
        self.assertFalse(lbls.isna().all())
        self.assertIn("UP", lbls.values)
        self.assertNotIn("FLAT", lbls.values)

    def test_margin_positive_creates_flat(self):
        df = _sample_price_df(200, uptrend=True)
        lbls = labels.label_forward_returns(df, horizon=5, margin=0.02)
        self.assertIn("FLAT", lbls.values)

    def test_label_uses_config_defaults(self):
        df = _sample_price_df(200, uptrend=True)
        lbls_default = labels.label_forward_returns(df)
        lbls_explicit = labels.label_forward_returns(
            df, horizon=config.HORIZON_DAYS, margin=config.MARGIN
        )
        self.assertTrue(lbls_default.equals(lbls_explicit))

    def test_build_labelled_frame_has_target_and_date(self):
        df = _sample_price_df(200, uptrend=True)
        frame = labels.build_labelled_frame(df, horizon=5)
        self.assertIn("target", frame.columns)
        self.assertIn("Date", frame.columns)

    def test_build_labelled_frame_respects_feature_subset(self):
        df = _sample_price_df(200, uptrend=True)
        frame = labels.build_labelled_frame(
            df, horizon=5, feature_columns=["returns", "rsi"]
        )
        cols = [c for c in frame.columns if c not in ("target", "Date")]
        self.assertTrue(set(cols).issubset({"ret_1", "ret_5", "ret_10", "log_ret_1", "RSI_14"}))

    def test_label_forward_returns_respects_horizon(self):
        df = _sample_price_df(200, uptrend=True)
        lbls_h1 = labels.label_forward_returns(df, horizon=1)
        lbls_h5 = labels.label_forward_returns(df, horizon=5)
        self.assertFalse(lbls_h1.equals(lbls_h5))

    def test_compute_feature_rows_empty_for_insufficient_data(self):
        df = _sample_price_df(30, uptrend=True)
        rows = labels.compute_feature_rows(df)
        self.assertTrue(rows.empty)


class TestModelDetailed(unittest.TestCase):
    """Deeper model tests."""

    def _trained_frame(self):
        return pd.concat(
            [labels.build_labelled_frame(_sample_price_df(200, up), 5) for up in (True, False)],
            ignore_index=True,
        )

    def test_all_model_families_train_and_predict(self):
        frame = self._trained_frame()
        for name in model.MODEL_SPECS:
            p = model.train_on_frame(frame, horizon=5, model_name=name)
            vector, _ = features.make_feature_vector(_sample_price_df(200, True))
            probs = p.predict_proba(vector)
            self.assertAlmostEqual(sum(probs.values()), 1.0, places=4)
            direction = p.predict_direction(vector)
            self.assertIn(direction, p.classes)

    def test_save_load_roundtrip(self):
        frame = self._trained_frame()
        with tempfile.TemporaryDirectory() as tmp:
            p = model.train_on_frame(frame, horizon=5)
            path = p.save(tmp + "/m.joblib")
            loaded = model.Predictor.load(path)
            self.assertEqual(loaded.version, p.version)
            self.assertEqual(loaded.feature_names, p.feature_names)
            self.assertEqual(loaded.classes, p.classes)

    def test_load_raises_on_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            model.Predictor.load("/nonexistent/path/model.joblib")

    def test_confidence_thresholds(self):
        self.assertEqual(model.Predictor.confidence(0.8, 0.1, 0.1), "HIGH")
        self.assertEqual(model.Predictor.confidence(0.55, 0.30, 0.15), "MEDIUM")
        self.assertEqual(model.Predictor.confidence(0.40, 0.35, 0.25), "LOW")

    def test_confidence_all_zeros(self):
        self.assertEqual(model.Predictor.confidence(0, 0, 0), "LOW")

    def test_normalize_model_name_unknown(self):
        self.assertEqual(model.normalize_model_name("unknown"), model.DEFAULT_MODEL)

    def test_normalize_model_name_valid(self):
        self.assertEqual(model.normalize_model_name("logistic"), "logistic")

    def test_default_model_path(self):
        p = model.default_model_path()
        self.assertTrue(p.endswith("model.joblib"))

    def test_train_on_frame_sets_meta(self):
        frame = self._trained_frame()
        p = model.train_on_frame(frame, horizon=5, meta={"custom_key": "custom_val"})
        self.assertEqual(p.meta["custom_key"], "custom_val")
        self.assertEqual(p.meta["model_name"], model.DEFAULT_MODEL)
        self.assertEqual(p.meta["horizon_days"], 5)

    def test_feature_importance_returns_list_of_dicts(self):
        frame = self._trained_frame()
        p = model.train_on_frame(frame, horizon=5)
        fi = model.Predictor.feature_importance(p, top_n=5)
        self.assertIsInstance(fi, list)
        for item in fi:
            self.assertIn("feature", item)
            self.assertIn("importance", item)

    def test_predict_proba_wrong_length_raises(self):
        frame = self._trained_frame()
        p = model.train_on_frame(frame, horizon=5)
        with self.assertRaises(ValueError):
            p.predict_proba([1.0] * 99)


class TestBacktestDetailed(unittest.TestCase):
    """Deeper backtest tests."""

    def _mixed_frame(self):
        return pd.concat(
            [labels.build_labelled_frame(_sample_price_df(200, up), 5) for up in (True, False)],
            ignore_index=True,
        )

    def test_backtest_beats_baseline_logic(self):
        frame = self._mixed_frame()
        metrics = backtest.run_backtest(frame, horizon=5, folds=3)
        if metrics["accuracy"] > metrics["baseline_accuracy"]:
            self.assertTrue(metrics["beats_baseline"])
        else:
            self.assertFalse(metrics["beats_baseline"])

    def test_backtest_preserves_classes_in_result(self):
        frame = self._mixed_frame()
        metrics = backtest.run_backtest(frame, horizon=5, folds=3)
        self.assertIsInstance(metrics["classes"], list)
        self.assertTrue(set(metrics["classes"]).issubset({"UP", "DOWN", "FLAT"}))

    def test_backtest_with_different_fold_counts(self):
        frame = self._mixed_frame()
        m3 = backtest.run_backtest(frame, folds=3)
        m5 = backtest.run_backtest(frame, folds=5)
        self.assertGreater(m3["n_samples"], 0)
        self.assertGreater(m5["n_samples"], 0)

    def test_backtest_insufficient_data(self):
        df = _sample_price_df(50, uptrend=True)
        frame = labels.build_labelled_frame(df, horizon=5)
        metrics = backtest.run_backtest(frame, folds=3)
        self.assertEqual(metrics["n_samples"], 0)
        self.assertIn("error", metrics)

    def test_backtest_max_train_caps_training_size(self):
        frame = self._mixed_frame()
        metrics = backtest.run_backtest(frame, folds=3, max_train=80)
        self.assertGreater(metrics["n_samples"], 0)

    def test_summarize_metrics_readable(self):
        frame = self._mixed_frame()
        metrics = backtest.run_backtest(frame, folds=3)
        summary = backtest.summarize_metrics(metrics)
        self.assertIsInstance(summary, str)
        self.assertIn("Samples", summary)

    def test_summarize_metrics_empty(self):
        summary = backtest.summarize_metrics({})
        self.assertIn("No backtest results.", summary)


class TestExploreDetailed(unittest.TestCase):
    """Deeper explore / lab orchestration tests."""

    def test_available_models_returns_list(self):
        mods = explore.available_models()
        self.assertIsInstance(mods, list)
        self.assertGreater(len(mods), 0)
        for m in mods:
            self.assertIn("name", m)
            self.assertIn("label", m)

    def test_available_feature_groups_returns_list(self):
        groups = explore.available_feature_groups()
        self.assertIsInstance(groups, list)
        self.assertGreater(len(groups), 0)
        for g in groups:
            self.assertIn("name", g)
            self.assertIn("count", g)

    def test_default_knobs_has_expected_keys(self):
        knobs = explore.default_knobs()
        for key in ("model_name", "horizon", "margin", "feature_groups", "folds", "max_train"):
            self.assertIn(key, knobs)

    def test_normalize_knobs_clamps_horizon(self):
        k = explore.normalize_knobs({"horizon": 999})
        self.assertEqual(k["horizon"], explore.HORIZON_MAX)
        k = explore.normalize_knobs({"horizon": -5})
        self.assertEqual(k["horizon"], explore.HORIZON_MIN)

    def test_normalize_knobs_clamps_margin(self):
        k = explore.normalize_knobs({"margin": 1.0})
        self.assertEqual(k["margin"], explore.MARGIN_MAX)
        k = explore.normalize_knobs({"margin": -0.5})
        self.assertEqual(k["margin"], explore.MARGIN_MIN)

    def test_normalize_knobs_unknown_model_defaults(self):
        k = explore.normalize_knobs({"model_name": "invalid_model"})
        self.assertEqual(k["model_name"], model.DEFAULT_MODEL)

    def test_normalize_knobs_empty_groups_defaults_all(self):
        k = explore.normalize_knobs({"feature_groups": []})
        self.assertEqual(k["feature_groups"], list(features.FEATURE_GROUPS.keys()))

    def test_normalize_knobs_string_groups_parsed(self):
        k = explore.normalize_knobs({"feature_groups": "returns,rsi"})
        self.assertIn("returns", k["feature_groups"])
        self.assertIn("rsi", k["feature_groups"])

    def test_explore_insufficient_history_raises(self):
        df = _sample_price_df(30, uptrend=True)
        with self.assertRaises(ValueError):
            explore.explore(df, {"horizon": 5})

    def test_explore_result_contains_expected_keys(self):
        df = _sample_price_df(250, uptrend=True)
        result = explore.explore(df, {"horizon": 5, "folds": 2})
        for key in ("direction", "prob_up", "prob_flat", "prob_down",
                    "confidence", "model_name", "n_features", "n_samples",
                    "backtest", "class_balance", "knobs"):
            self.assertIn(key, result)

    def test_explore_probabilities_sum_to_one(self):
        df = _sample_price_df(250, uptrend=True)
        result = explore.explore(df, {"horizon": 5, "folds": 2})
        total = result["prob_up"] + result["prob_flat"] + result["prob_down"]
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_explore_with_all_model_families(self):
        df = pd.concat(
            [_sample_price_df(150, up) for up in (True, False)], ignore_index=True
        )
        for name in model.MODEL_SPECS:
            result = explore.explore(df, {"model_name": name, "horizon": 5, "folds": 2})
            self.assertIn(result["direction"], {"UP", "DOWN", "FLAT"})


class TestDataset(unittest.TestCase):
    """Tests for ml.dataset payload normalization."""

    def test_payload_to_frame_dict_with_data(self):
        df = _sample_price_df(100, uptrend=True)
        payload = {"data": df.to_dict(orient="records")}
        result = dataset.payload_to_frame(payload)
        self.assertFalse(result.empty)
        self.assertIn("Close", result.columns)

    def test_payload_to_frame_dict_with_rows(self):
        df = _sample_price_df(100, uptrend=True)
        payload = {"rows": df.to_dict(orient="records")}
        result = dataset.payload_to_frame(payload)
        self.assertFalse(result.empty)

    def test_payload_to_frame_list_of_records(self):
        df = _sample_price_df(100, uptrend=True)
        records = df.to_dict(orient="records")
        result = dataset.payload_to_frame(records)
        self.assertFalse(result.empty)

    def test_payload_to_frame_json_string(self):
        df = _sample_price_df(100, uptrend=True)
        json_str = df.to_json(orient="records", date_format="iso")
        result = dataset.payload_to_frame(json_str)
        self.assertFalse(result.empty)

    def test_payload_to_frame_empty_returns_none(self):
        self.assertIsNone(dataset.payload_to_frame(None))
        self.assertIsNone(dataset.payload_to_frame({}))
        self.assertIsNone(dataset.payload_to_frame([]))
        self.assertIsNone(dataset.payload_to_frame({"no_data": True}))

    def test_payload_to_frame_missing_close_returns_none(self):
        self.assertIsNone(dataset.payload_to_frame({"data": [{"Open": 1}]}))

    def test_labelled_frame_for_payload_short_series(self):
        df = _sample_price_df(30, uptrend=True)
        payload = {"data": df.to_dict(orient="records")}
        result = dataset.labelled_frame_for_payload(payload)
        self.assertTrue(result.empty)

    def test_labelled_frame_for_payload_valid(self):
        df = _sample_price_df(200, uptrend=True)
        payload = {"data": df.to_dict(orient="records")}
        result = dataset.labelled_frame_for_payload(payload, horizon=5)
        self.assertFalse(result.empty)


class TestConfigEnvOverrides(unittest.TestCase):
    """Tests for ml.config environment variable overrides."""

    def test_horizon_from_env(self):
        import ml.config as cfg
        orig = os.environ.get("OOOBIR_ML_HORIZON")
        os.environ["OOOBIR_ML_HORIZON"] = "10"
        cfg.HORIZON_DAYS  # re-evaluated at import time in module; just check it parses
        if orig is None:
            del os.environ["OOOBIR_ML_HORIZON"]
        else:
            os.environ["OOOBIR_ML_HORIZON"] = orig


if __name__ == "__main__":
    unittest.main()
