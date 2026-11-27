"""Offline unit tests for the ML training CLI and module entrypoint."""

import json
import runpy
import sys
import tempfile
import unittest
import warnings
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from ml import config, train


class TestMLTrainHelpers(unittest.TestCase):
    """Pure helpers that need no files, models or network."""

    def test_sample_universe_subset_is_deterministic(self):
        names = [f"T{i:03d}" for i in range(20)]
        with patch.object(train.dataset, "ticker_filenames", return_value=names):
            first = train._sample_universe(5)
            second = train._sample_universe(5)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)
        self.assertEqual(first, sorted(first))
        self.assertTrue(set(first).issubset(names))

    def test_sample_universe_none_or_large_returns_all_names(self):
        names = ["AAA", "BBB", "CCC"]
        with patch.object(train.dataset, "ticker_filenames", return_value=names):
            self.assertEqual(train._sample_universe(None), names)
            self.assertEqual(train._sample_universe(100), names)

    def test_historical_path_uses_expected_filename(self):
        self.assertEqual(
            Path(train._historical_path("AAPL")).name,
            "AAPL_price_history_all.json",
        )


class TestBuildTrainingFrame(unittest.TestCase):
    """Stored, invalid and live payloads are combined without network access."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.path_patch = patch.object(
            train,
            "_historical_path",
            side_effect=lambda ticker: str(self.root / f"{ticker}.json"),
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def _write(self, ticker, text):
        (self.root / f"{ticker}.json").write_text(text, encoding="utf-8")

    def test_no_payloads_returns_empty_frame(self):
        with (
            patch.object(train.dataset, "labelled_frame_for_payload") as labelled,
            patch.object(train, "_fetch_live_payload") as fetch,
        ):
            result = train.build_training_frame(["MISSING"], live=False)
        self.assertTrue(result.empty)
        labelled.assert_not_called()
        fetch.assert_not_called()

    def test_stored_payloads_are_concatenated_with_ticker_column(self):
        self._write("AAA", '[{"Close": 10}]')
        self._write("BBB", '[{"Close": 20}]')
        frames = [
            pd.DataFrame({"Close": [10, 11], "target": ["UP", "DOWN"]}),
            pd.DataFrame({"Close": [20, 21], "target": ["UP", "UP"]}),
        ]
        with (
            patch.object(
                train.dataset, "labelled_frame_for_payload", side_effect=frames
            ) as labelled,
            patch.object(train, "_fetch_live_payload") as fetch,
        ):
            result = train.build_training_frame(["AAA", "BBB"])
        self.assertEqual(list(result["ticker"]), ["AAA", "AAA", "BBB", "BBB"])
        self.assertEqual(list(result["Close"]), [10, 11, 20, 21])
        self.assertEqual(labelled.call_count, 2)
        fetch.assert_not_called()

    def test_invalid_json_falls_back_to_live_only_when_requested(self):
        self._write("AAA", "not json")
        live_payload = [{"Close": 30}]
        frame = pd.DataFrame({"Close": [30, 31], "target": ["UP", "UP"]})
        with (
            patch.object(
                train, "_fetch_live_payload", return_value=live_payload
            ) as fetch,
            patch.object(
                train.dataset, "labelled_frame_for_payload", return_value=frame
            ) as labelled,
        ):
            result = train.build_training_frame(["AAA"], live=True)
            fetch.assert_called_once_with("AAA")
            labelled.assert_called_once_with(live_payload, None)
            self.assertEqual(list(result["ticker"]), ["AAA", "AAA"])
        with patch.object(train, "_fetch_live_payload") as fetch:
            self.assertTrue(train.build_training_frame(["AAA"]).empty)
            fetch.assert_not_called()

    def test_live_failure_and_empty_labelled_frame_are_skipped(self):
        with (
            patch.object(train, "_fetch_live_payload", return_value=None),
            patch.object(train.dataset, "labelled_frame_for_payload") as labelled,
        ):
            self.assertTrue(train.build_training_frame(["AAA"], live=True).empty)
            labelled.assert_not_called()
        self._write("AAA", '[{"Close": 10}]')
        with (
            patch.object(train, "_fetch_live_payload") as fetch,
            patch.object(
                train.dataset, "labelled_frame_for_payload", return_value=pd.DataFrame()
            ),
        ):
            self.assertTrue(train.build_training_frame(["AAA"]).empty)
            fetch.assert_not_called()


class TestFetchLivePayload(unittest.TestCase):
    """yfinance is replaced with a fake module; no HTTP calls are made."""

    @staticmethod
    def _fake_yfinance(history=None, error=None):
        yf = MagicMock()
        ticker = MagicMock()
        if error is not None:
            yf.Ticker.side_effect = error
        else:
            yf.Ticker.return_value = ticker
            ticker.history.return_value = history
        return yf, ticker

    def test_successful_fetch_parses_table_json(self):
        history = MagicMock(empty=False)
        history.to_json.return_value = '[{"Close": 10}]'
        yf, ticker = self._fake_yfinance(history=history)
        with patch.dict(sys.modules, {"yfinance": yf}):
            result = train._fetch_live_payload("AAPL")
        self.assertEqual(result, [{"Close": 10}])
        yf.Ticker.assert_called_once_with("AAPL")
        ticker.history.assert_called_once_with(period="5y")
        history.to_json.assert_called_once_with(orient="table")

    def test_none_or_empty_history_returns_none(self):
        for history in (None, MagicMock(empty=True)):
            yf, _ = self._fake_yfinance(history=history)
            with patch.dict(sys.modules, {"yfinance": yf}):
                self.assertIsNone(train._fetch_live_payload("AAPL"))

    def test_provider_error_returns_none(self):
        yf, _ = self._fake_yfinance(error=RuntimeError("offline"))
        with patch.dict(sys.modules, {"yfinance": yf}):
            self.assertIsNone(train._fetch_live_payload("AAPL"))


class TestTrainFromData(unittest.TestCase):
    """Training is mocked so nothing is fitted or written to disk."""

    def test_empty_frame_exits(self):
        with self.assertRaises(SystemExit):
            train.train_from_data(pd.DataFrame())

    def test_trains_saves_and_prints_backtest_summary(self):
        frame = pd.DataFrame({"Close": [1, 2]})
        predictor = MagicMock(
            version="v-test", trained_on="2026-01-01", meta={"rows": 2}, classes=["UP"]
        )
        predictor.save.return_value = "/tmp/model.joblib"
        metrics = {"accuracy": 0.7}
        with (
            patch.object(train.model, "train_on_frame", return_value=predictor) as fit,
            patch.object(train, "run_backtest", return_value=metrics) as backtest_mock,
            patch.object(
                train, "summarize_metrics", return_value="METRICS"
            ) as summarize,
            redirect_stdout(StringIO()) as output,
        ):
            result = train.train_from_data(frame, horizon=3)
        self.assertIs(result, predictor)
        fit.assert_called_once_with(frame, horizon=3)
        predictor.save.assert_called_once_with()
        backtest_mock.assert_called_once_with(frame, horizon=3)
        summarize.assert_called_once_with(metrics)
        for expected in (
            "Saved model -> /tmp/model.joblib",
            "Model version: v-test",
            "Trained on   : 2026-01-01",
            "Rows         : 2",
            "Classes      : ['UP']",
            "=== Walk-forward backtest ===",
            "METRICS",
        ):
            self.assertIn(expected, output.getvalue())


class TestPredictTicker(unittest.TestCase):
    """Stored and live payload paths are exercised with mocked predictors."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.path_patch = patch.object(
            train,
            "_historical_path",
            side_effect=lambda ticker: str(self.root / f"{ticker}.json"),
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def test_stored_payload_is_converted_and_predicted(self):
        (self.root / "AAA.json").write_text('[{"Close": 10}]', encoding="utf-8")
        frame = pd.DataFrame({"Close": [10]})
        expected = {"symbol": "AAA", "direction": "UP"}
        with (
            patch.object(
                train.dataset, "payload_to_frame", return_value=frame
            ) as convert,
            patch.object(
                train, "_predict_from_frame", return_value=expected
            ) as predict,
        ):
            result = train.predict_ticker("AAA", horizon=2)
        self.assertEqual(result, expected)
        convert.assert_called_once_with([{"Close": 10}])
        predict.assert_called_once_with("AAA", frame, 2)

    def test_live_fallback_is_used_when_no_stored_file(self):
        payload = [{"Close": 20}]
        frame = pd.DataFrame({"Close": [20]})
        with (
            patch.object(train, "_fetch_live_payload", return_value=payload) as fetch,
            patch.object(train.dataset, "payload_to_frame", return_value=frame),
            patch.object(train, "_predict_from_frame", return_value={"symbol": "BBB"}),
        ):
            result = train.predict_ticker("BBB", live=True)
        self.assertEqual(result, {"symbol": "BBB"})
        fetch.assert_called_once_with("BBB")

    def test_missing_file_raises_even_with_live_disabled(self):
        with patch.object(train, "_fetch_live_payload") as fetch:
            with self.assertRaisesRegex(FileNotFoundError, "No stored history for AAA"):
                train.predict_ticker("AAA")
            fetch.assert_not_called()

    def test_failed_live_fetch_raises_file_not_found(self):
        with (
            patch.object(train, "_fetch_live_payload", return_value=None),
            self.assertRaises(FileNotFoundError),
        ):
            train.predict_ticker("AAA", live=True)


class TestPredictFromFrame(unittest.TestCase):
    """Prediction dict assembly uses a fake loaded model."""

    def setUp(self):
        self.frame = pd.DataFrame({"Close": list(range(200))})
        self.predictor = MagicMock(version="v1")
        self.predictor.predict_proba.return_value = {
            "UP": 0.5,
            "FLAT": 0.2,
            "DOWN": 0.3,
        }
        self.predictor.predict_direction.return_value = "UP"
        self.predictor.confidence.return_value = "MEDIUM"

    def test_short_or_missing_history_is_rejected(self):
        for frame in (None, pd.DataFrame({"Close": [1, 2]})):
            with (
                patch.object(config, "MIN_HISTORY", 120),
                self.assertRaisesRegex(ValueError, "need >= 120 rows"),
            ):
                train._predict_from_frame("AAA", frame)

    def test_result_contains_probabilities_horizon_and_confidence(self):
        vector = [0.1, 0.2]
        with (
            patch.object(config, "MIN_HISTORY", 120),
            patch.object(
                train.model.Predictor, "load", return_value=self.predictor
            ) as load,
            patch.object(
                train.features, "make_feature_vector", return_value=(vector, None)
            ) as make,
        ):
            result = train._predict_from_frame("AAA", self.frame, horizon=7)
        load.assert_called_once_with()
        make.assert_called_once_with(self.frame)
        self.predictor.predict_proba.assert_called_once_with(vector)
        self.predictor.predict_direction.assert_called_once_with(vector)
        self.predictor.confidence.assert_called_once_with(0.5, 0.3, 0.2)
        self.assertEqual(
            result,
            {
                "symbol": "AAA",
                "direction": "UP",
                "probability": 0.5,
                "prob_up": 0.5,
                "prob_flat": 0.2,
                "prob_down": 0.3,
                "horizon_days": 7,
                "confidence": "MEDIUM",
                "model_version": "v1",
            },
        )

    def test_default_horizon_comes_from_config(self):
        with (
            patch.object(config, "MIN_HISTORY", 120),
            patch.object(config, "HORIZON_DAYS", 5),
            patch.object(train.model.Predictor, "load", return_value=self.predictor),
            patch.object(
                train.features, "make_feature_vector", return_value=([1], None)
            ),
        ):
            result = train._predict_from_frame("AAA", self.frame)
        self.assertEqual(result["horizon_days"], 5)


class TestTrainCLI(unittest.TestCase):
    """Each subcommand is driven through mocked helpers."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_train_passes_options_and_saves_only_with_flag(self):
        frame = pd.DataFrame({"Close": [1]})
        predictor = MagicMock()
        for extra, expected_saves in (([], 0), (["--save"], 1)):
            predictor.reset_mock()
            with (
                patch.object(train, "_sample_universe", return_value=["AAA"]) as sample,
                patch.object(
                    train, "build_training_frame", return_value=frame
                ) as build,
                patch.object(train, "train_from_data", return_value=predictor) as fit,
                redirect_stdout(StringIO()),
            ):
                train._cli(["train", "--size", "1", "--horizon", "4", "--live", *extra])
            sample.assert_called_once_with(1)
            build.assert_called_once_with(["AAA"], 4, live=True)
            fit.assert_called_once_with(frame, 4)
            self.assertEqual(predictor.save.call_count, expected_saves)

    def test_predict_prints_json_result(self):
        result = {"symbol": "AAA", "direction": "UP"}
        with (
            patch.object(train, "predict_ticker", return_value=result) as predict,
            redirect_stdout(StringIO()) as output,
        ):
            train._cli(["predict", "--ticker", "AAA", "--horizon", "2", "--live"])
        predict.assert_called_once_with("AAA", 2, live=True)
        self.assertEqual(json.loads(output.getvalue()), result)

    def _run_backtest_cli(self, path, live=False):
        payload = [{"Close": 10}]
        frame = pd.DataFrame({"Close": [10]})
        label = "AAA"
        if path is not None:
            (self.root / f"{label}.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )
        with (
            patch.object(
                train,
                "_historical_path",
                return_value=str(self.root / f"{label}.json"),
            ),
            patch.object(train, "_fetch_live_payload", return_value=payload) as fetch,
            patch.object(
                train.dataset, "labelled_frame_for_payload", return_value=frame
            ) as labelled,
            patch.object(
                train, "run_backtest", return_value={"accuracy": 0.6}
            ) as backtest_mock,
            patch.object(
                train, "summarize_metrics", return_value="SUMMARY"
            ) as summarize,
            redirect_stdout(StringIO()) as output,
        ):
            args = ["backtest", "--ticker", label, "--horizon", "3"]
            if live:
                args.append("--live")
            train._cli(args)
        return (
            fetch,
            labelled,
            backtest_mock,
            summarize,
            output.getvalue(),
            payload,
            frame,
        )

    def test_backtest_uses_stored_payload(self):
        fetch, labelled, backtest_mock, summarize, output, payload, frame = (
            self._run_backtest_cli(path=True)
        )
        fetch.assert_not_called()
        labelled.assert_called_once_with(payload, 3)
        backtest_mock.assert_called_once_with(frame, horizon=3)
        summarize.assert_called_once_with({"accuracy": 0.6})
        self.assertIn("SUMMARY", output)

    def test_backtest_live_fallback_when_file_missing(self):
        fetch, labelled, _, _, _, _, _ = self._run_backtest_cli(path=None, live=True)
        fetch.assert_called_once_with("AAA")
        labelled.assert_called_once()

    def test_backtest_missing_payload_exits(self):
        with (
            patch.object(
                train, "_historical_path", return_value=str(self.root / "absent.json")
            ),
            patch.object(train, "_fetch_live_payload", return_value=None),
            self.assertRaisesRegex(SystemExit, "No stored history for AAA"),
        ):
            train._cli(["backtest", "--ticker", "AAA"])


class TestModuleEntrypoint(unittest.TestCase):
    """``python -m ml`` delegates argv to the CLI without side effects."""

    def test_main_module_calls_cli_with_arguments(self):
        with (
            patch.object(train, "_cli") as cli,
            patch.object(sys, "argv", ["ml", "predict", "--ticker", "AAA"]),
        ):
            runpy.run_module("ml", run_name="__main__")
        cli.assert_called_once_with(["predict", "--ticker", "AAA"])

    def test_importing_module_does_not_call_cli(self):
        with patch.object(train, "_cli") as cli:
            runpy.run_module("ml", run_name="ml.__main__")
        cli.assert_not_called()

    def test_train_module_runs_cli_as_a_script(self):
        with (
            warnings.catch_warnings(),
            patch.object(sys, "argv", ["ml.train", "--help"]),
            redirect_stdout(StringIO()),
            self.assertRaises(SystemExit) as ctx,
        ):
            warnings.filterwarnings(
                "ignore", ".*found in sys.modules.*", RuntimeWarning
            )
            runpy.run_module("ml.train", run_name="__main__")
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
