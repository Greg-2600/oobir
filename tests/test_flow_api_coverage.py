"""Focused coverage tests for flow_api.py branches and error paths."""

import concurrent.futures
import json
import os
import sys
import unittest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import requests
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestSerializeValueBranches(unittest.TestCase):
    """Cover serialization branches used by cache and API responses."""

    def test_serialize_date_and_datetime(self):
        self.assertEqual(flow_api.serialize_value(date(2024, 1, 2)), "2024-01-02")
        self.assertEqual(
            flow_api.serialize_value(datetime(2024, 1, 2, 3, 4, 5)),
            "2024-01-02T03:04:05",
        )

    def test_serialize_nan_and_infinity(self):
        self.assertIsNone(flow_api.serialize_value(float("nan")))
        self.assertEqual(flow_api.serialize_value(float("inf")), "Infinity")
        self.assertEqual(flow_api.serialize_value(float("-inf")), "-Infinity")

    def test_serialize_pandas_temporal_types(self):
        timestamp = pd.Timestamp("2024-01-02T03:04:05")
        self.assertEqual(flow_api.serialize_value(timestamp), timestamp.isoformat())
        self.assertEqual(
            flow_api.serialize_value(pd.Timedelta("1 day")),
            pd.Timedelta("1 day").isoformat(),
        )


class TestAppLifecycleAndSystemEndpoints(unittest.TestCase):
    """Cover lifespan startup/shutdown and basic system endpoints."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    def test_lifespan_runs_startup_and_shutdown(self):
        with TestClient(flow_api.app) as client:
            response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)

    @patch("db.get_cache_stats")
    def test_cache_info_endpoint(self, mock_stats):
        mock_stats.return_value = {"entries": 5}
        response = self.client.get("/api/cache-info")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"entries": 5})

    @patch("db.clear_cache")
    def test_cache_flush_endpoint(self, mock_clear):
        mock_clear.return_value = 3
        response = self.client.post("/api/cache-flush?endpoint=news&symbol=AAPL")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cleared"], 3)
        mock_clear.assert_called_once_with(endpoint="news", symbol="AAPL")

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["docs"], "/docs")


class TestOllamaHealthBranches(unittest.TestCase):
    """Cover all error paths of the Ollama health check."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("requests.get")
    def test_non_200_response_is_degraded(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        response = self.client.get("/health/ollama")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")

    @patch("requests.get")
    def test_timeout_is_unhealthy(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        response = self.client.get("/health/ollama")
        self.assertEqual(response.status_code, 503)
        self.assertIn("Timeout", response.json()["error"])

    @patch("requests.get")
    def test_connection_error_is_unhealthy(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        response = self.client.get("/health/ollama")
        self.assertEqual(response.status_code, 503)
        self.assertIn("Cannot connect", response.json()["error"])

    @patch("requests.get")
    def test_unexpected_error_is_unhealthy(self, mock_get):
        mock_get.side_effect = RuntimeError("unexpected")
        response = self.client.get("/health/ollama")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "unexpected")


class TestHealthDepsBranches(unittest.TestCase):
    """Cover degraded dependency combinations in /health/deps."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    def _healthy_conn(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    def test_ollama_exception_degrades(self):
        with (
            patch("requests.get", side_effect=RuntimeError("offline")),
            patch("db.get_cache_stats", return_value={"entries": 1}),
            patch("db_timescale.get_conn", return_value=self._healthy_conn()),
            patch("yfinance.Ticker") as mock_ticker,
        ):
            mock_ticker.return_value.fast_info = {}
            response = self.client.get("/health/deps")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")

    def test_cache_exception_degrades(self):
        with (
            patch("requests.get", return_value=MagicMock(status_code=200)),
            patch("db.get_cache_stats", side_effect=RuntimeError("cache down")),
            patch("db_timescale.get_conn", return_value=self._healthy_conn()),
            patch("yfinance.Ticker") as mock_ticker,
        ):
            mock_ticker.return_value.fast_info = {}
            response = self.client.get("/health/deps")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["dependencies"]["cache"]["status"], "degraded")

    def test_timescale_exception_degrades(self):
        with (
            patch("requests.get", return_value=MagicMock(status_code=200)),
            patch("db.get_cache_stats", return_value={"entries": 1}),
            patch("db_timescale.is_configured", return_value=True),
            patch("db_timescale.get_conn", side_effect=RuntimeError("db down")),
            patch("yfinance.Ticker") as mock_ticker,
        ):
            mock_ticker.return_value.fast_info = {}
            response = self.client.get("/health/deps")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["dependencies"]["timescale"]["status"], "degraded"
        )

    def test_yfinance_exception_reports_degraded_but_healthy(self):
        with (
            patch("requests.get", return_value=MagicMock(status_code=200)),
            patch("db.get_cache_stats", return_value={"entries": 1}),
            patch("db_timescale.get_conn", return_value=self._healthy_conn()),
            patch("yfinance.Ticker", side_effect=RuntimeError("yahoo down")),
        ):
            response = self.client.get("/health/deps")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["dependencies"]["yfinance"]["status"], "degraded"
        )


class TestCacheWrappers(unittest.TestCase):
    """Cover cache hits and payload normalization paths."""

    @patch("db.get_cached_data", return_value={"symbol": "AAPL"})
    def test_with_cache_returns_cached_without_calling_flow(self, _mock_get):
        flow_function = MagicMock()
        result = flow_api.with_cache("fundamentals", "AAPL", flow_function)
        self.assertEqual(result, {"symbol": "AAPL"})
        flow_function.assert_not_called()

    @patch("db.get_cached_data")
    @patch("db.set_cached_data")
    def test_price_history_cached_payload_is_trimmed(self, mock_set, mock_get):
        rows = [{"Date": f"2024-01-{idx:03d}", "Close": idx} for idx in range(150)]
        mock_get.return_value = {"data": rows}
        result = flow_api.get_price_history_payload("AAPL")
        self.assertEqual(len(result["data"]), flow_api.PRICE_HISTORY_WINDOW)
        mock_set.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.fetch_price_history")
    @patch("db_timescale.get_conn")
    def test_price_history_prefers_timescale_rows(
        self, mock_get_conn, mock_fetch, mock_set, _mock_get
    ):
        mock_fetch.return_value = [{"Date": "2024-01-02", "Close": 101.0}]
        result = flow_api.get_price_history_payload("AAPL")
        self.assertEqual(result["data"][0]["Close"], 101.0)
        mock_get_conn.return_value.close.assert_called_once()
        mock_set.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_price_history")
    @patch("db_timescale.get_conn", side_effect=RuntimeError("db down"))
    def test_price_history_falls_back_to_json_flow_result(
        self, _mock_conn, mock_history, _mock_set, _mock_get
    ):
        mock_history.return_value = json.dumps(
            {"data": [{"Date": "2024-01-02", "Close": 101.0}]}
        )
        result = flow_api.get_price_history_payload("AAPL")
        self.assertEqual(result["data"][0]["Close"], 101.0)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.ensure_ollama")
    def test_with_ai_cache_keeps_malformed_json_as_string(
        self, _mock_ensure, _mock_set, _mock_get
    ):
        result = flow_api.with_ai_cache(
            "ai-test", "AAPL", lambda _symbol: "{not valid json"
        )
        self.assertEqual(result, "{not valid json")


class TestPureHelpers(unittest.TestCase):
    """Cover small helper branches not exercised by endpoint tests."""

    def test_extract_fundamentals_payload_non_dict(self):
        self.assertEqual(
            flow_api._extract_fundamentals_payload(None, "AAPL"), {"symbol": "AAPL"}
        )

    def test_extract_fundamentals_payload_adds_symbol(self):
        result = flow_api._extract_fundamentals_payload({"currentPrice": 10}, "AAPL")
        self.assertEqual(result["symbol"], "AAPL")

    def test_to_float_invalid_values(self):
        self.assertEqual(flow_api._to_float("not-a-number", default=7.0), 7.0)
        self.assertEqual(flow_api._to_float(object(), default=3.0), 3.0)

    def test_feature_vector_uses_current_price_when_previous_missing(self):
        result = flow_api._feature_vector({"currentPrice": 10.0})
        self.assertEqual(result["price"], 10.0)
        self.assertEqual(result["change_pct"], 0.0)

    def test_similarity_reason_both_pay_dividends(self):
        base = {
            "price": 1.0,
            "change_pct": 0.0,
            "volume": 1.0,
            "has_dividend": True,
        }
        candidate = {
            "price": 10.0,
            "change_pct": 100.0,
            "volume": 1000.0,
            "has_dividend": True,
        }
        self.assertEqual(
            flow_api._similarity_reason(base, candidate), "both pay dividends"
        )

    def test_similarity_reason_default_when_nothing_matches(self):
        base = {
            "price": 1.0,
            "change_pct": 0.0,
            "volume": 1.0,
            "has_dividend": True,
        }
        candidate = {
            "price": 1000.0,
            "change_pct": 100.0,
            "volume": 1_000_000_000.0,
            "has_dividend": False,
        }
        self.assertEqual(
            flow_api._similarity_reason(base, candidate),
            "overlapping price/volume profile",
        )

    def test_compute_rsi_with_gains_and_losses(self):
        closes = [100 + (idx % 3) for idx in range(20)]
        rsi = flow_api._compute_rsi(closes)
        self.assertIsNotNone(rsi)
        self.assertGreaterEqual(rsi, 0.0)
        self.assertLessEqual(rsi, 100.0)

    def test_parse_portfolio_tickers_deduplicates(self):
        result = flow_api._parse_portfolio_tickers("AAPL,MSFT,MSFT,NVDA,AAPL", "AAPL")
        self.assertEqual(result, ["MSFT", "NVDA"])

    def test_extract_close_series_accepts_list_and_skips_invalid_rows(self):
        payload = [
            {"Close": 10.0},
            {"close": 11.0},
            "not-a-row",
            {"Close": 0},
        ]
        self.assertEqual(flow_api._extract_close_series(payload), [10.0, 11.0])


class TestFundamentalsPayloadBranches(unittest.TestCase):
    """Cover DB-first fundamentals normalization and fallback paths."""

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.fetch_latest_fundamentals")
    @patch("db_timescale.get_conn")
    def test_fundamentals_from_raw_info_with_legacy_aliases(
        self, _mock_conn, mock_fetch, mock_set, _mock_get
    ):
        mock_fetch.return_value = {
            "raw_info": {"trailingPE": 20.0, "marketCap": 1000.0, "currentPrice": 5.0}
        }
        result = flow_api.get_fundamentals_payload("AAPL")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["pe_ratio"], 20.0)
        self.assertEqual(result["market_cap"], 1000.0)
        mock_set.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db_timescale.get_conn", side_effect=RuntimeError("db down"))
    @patch("flow_api.with_cache", return_value='{"symbol": "AAPL"}')
    def test_fundamentals_parses_json_string_from_cache_wrapper(
        self, _mock_with_cache, _mock_conn, _mock_get
    ):
        result = flow_api.get_fundamentals_payload("AAPL")
        self.assertEqual(result, {"symbol": "AAPL"})


class TestRelatedStocksBranches(unittest.TestCase):
    """Cover fallback and filtering branches in related stocks."""

    @patch("flow.get_fundamentals")
    @patch("db_timescale.fetch_latest_fundamentals_bulk", return_value={})
    @patch("db_timescale.list_fundamental_tickers", return_value=[])
    @patch("db_timescale.fetch_latest_fundamentals", return_value=None)
    @patch("db_timescale.get_conn")
    def test_related_stocks_falls_back_to_flow_fundamentals(
        self, _mock_conn, _mock_fetch, _mock_tickers, _mock_bulk, mock_flow
    ):
        mock_flow.return_value = json.dumps(
            {
                "symbol": "AAPL",
                "currentPrice": 100.0,
                "previousClose": 99.0,
                "volume": 1000,
            }
        )
        result = flow_api.get_related_stocks_payload("AAPL", 3, "")
        self.assertEqual(result, {"symbol": "AAPL", "related": []})

    @patch("db_timescale.fetch_latest_fundamentals_bulk")
    @patch("db_timescale.list_fundamental_tickers", return_value=["ZERO", "OK"])
    @patch("db_timescale.fetch_latest_fundamentals")
    @patch("db_timescale.get_conn")
    def test_related_stocks_skips_candidates_without_price(
        self, _mock_conn, mock_fetch, _mock_tickers, mock_bulk
    ):
        mock_fetch.return_value = {
            "symbol": "AAPL",
            "currentPrice": 100.0,
            "previousClose": 99.0,
            "volume": 1000,
        }
        mock_bulk.return_value = {
            "ZERO": {"symbol": "ZERO"},
            "OK": {
                "symbol": "OK",
                "currentPrice": 101.0,
                "previousClose": 100.0,
                "volume": 2000,
            },
        }
        result = flow_api.get_related_stocks_payload("AAPL", 3, "")
        tickers = [row["ticker"] for row in result["related"]]
        self.assertNotIn("ZERO", tickers)
        self.assertIn("OK", tickers)


class TestDecisionEngineBranches(unittest.TestCase):
    """Exercise valuation, momentum, volatility and risk action branches."""

    def _price_payload(self, closes):
        return {"data": [{"Close": value} for value in closes]}

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_valuation_between_30_and_45(self, mock_fund, mock_price):
        mock_fund.return_value = {"trailingPE": 35.0, "returnOnEquity": 0.12}
        mock_price.return_value = self._price_payload([100.0] * 60)
        result = flow_api.get_decision_engine_payload("AAPL")
        self.assertEqual(result["component_scores"]["valuation"], -10.0)

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_stretched_valuation_and_negative_momentum_reduce_risk(
        self, mock_fund, mock_price
    ):
        mock_fund.return_value = {"trailingPE": 50.0, "returnOnEquity": 0.0}
        mock_price.return_value = self._price_payload(
            [100.0 - idx * 0.5 for idx in range(60)]
        )
        result = flow_api.get_decision_engine_payload("AAPL")
        self.assertEqual(result["action"], "REDUCE_RISK")
        self.assertIn("MOMENTUM_NEGATIVE", result["reason_codes"])
        self.assertIn("VALUATION_STRETCHED", result["reason_codes"])
        self.assertTrue(result["risk_gates"]["valuation_stretched"])
        self.assertTrue(
            any("Valuation is stretched" in note for note in result["risk_notes"])
        )

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_high_volatility_blocks_action(self, mock_fund, mock_price):
        mock_fund.return_value = {"trailingPE": 20.0}
        closes = []
        value = 100.0
        for idx in range(60):
            value *= 1.10 if idx % 2 == 0 else 0.90
            closes.append(value)
        mock_price.return_value = self._price_payload(closes)
        result = flow_api.get_decision_engine_payload("AAPL")
        self.assertEqual(result["action"], "WAIT")
        self.assertTrue(result["risk_gates"]["volatility_high"])
        self.assertIn("VOLATILITY_HIGH", result["reason_codes"])
        self.assertTrue(
            any("Volatility is elevated" in note for note in result["risk_notes"])
        )


class TestExploreCacheHelpers(unittest.TestCase):
    """Cover the in-memory explore cache hit and eviction paths."""

    def setUp(self):
        flow_api._ML_EXPLORE_CACHE.clear()

    def tearDown(self):
        flow_api._ML_EXPLORE_CACHE.clear()

    def test_cache_get_returns_and_moves_existing_entry(self):
        flow_api._explore_cache_put("key", {"cached": True})
        self.assertEqual(flow_api._explore_cache_get("key"), {"cached": True})
        self.assertIsNone(flow_api._explore_cache_get("missing"))

    def test_cache_put_evicts_oldest_entry_when_full(self):
        with patch.object(flow_api, "_ML_EXPLORE_CACHE_MAX", 1):
            flow_api._explore_cache_put("first", {"value": 1})
            flow_api._explore_cache_put("second", {"value": 2})
        self.assertNotIn("first", flow_api._ML_EXPLORE_CACHE)
        self.assertIn("second", flow_api._ML_EXPLORE_CACHE)


class TestMlPriceHistoryBranches(unittest.TestCase):
    """Cover ML history caching, DB preference and yfinance fallback."""

    @patch("db.get_cached_data", return_value={"data": [{"Close": 1.0}]})
    def test_cached_payload_returned(self, _mock_get):
        self.assertEqual(
            flow_api.get_ml_price_history_payload("AAPL"),
            {"data": [{"Close": 1.0}]},
        )

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.fetch_price_history")
    @patch("db_timescale.get_conn")
    def test_timescale_rows_are_cached(
        self, _mock_conn, mock_fetch, mock_set, _mock_get
    ):
        mock_fetch.return_value = [{"Date": "2024-01-02", "Close": 101.0}]
        result = flow_api.get_ml_price_history_payload("AAPL")
        self.assertEqual(result["data"][0]["Close"], 101.0)
        mock_set.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("yfinance.Ticker")
    @patch("db_timescale.get_conn", side_effect=RuntimeError("db down"))
    def test_yfinance_fallback_when_db_fails(
        self, _mock_conn, mock_ticker, mock_set, _mock_get
    ):
        mock_ticker.return_value.history.return_value.to_json.return_value = (
            '{"data": [{"Close": 101.0}]}'
        )
        result = flow_api.get_ml_price_history_payload("AAPL")
        self.assertEqual(result["data"][0]["Close"], 101.0)
        mock_set.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("yfinance.Ticker", side_effect=RuntimeError("yahoo down"))
    @patch("db_timescale.get_conn", side_effect=RuntimeError("db down"))
    def test_returns_none_when_db_and_yfinance_fail(
        self, _mock_conn, _mock_ticker, _mock_get
    ):
        self.assertIsNone(flow_api.get_ml_price_history_payload("AAPL"))


class TestMlEndpointErrorBranches(unittest.TestCase):
    """Cover ML endpoint caching and unexpected-error branches."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("flow_api._ml_price_frame", side_effect=RuntimeError("bad frame"))
    def test_predict_unexpected_error_returns_500(self, _mock_frame):
        response = self.client.get("/api/predict/AAPL")
        self.assertEqual(response.status_code, 500)

    @patch("db.get_cached_data", return_value={"accuracy": 0.5})
    def test_backtest_returns_cached_metrics(self, _mock_get):
        response = self.client.get("/api/predict/AAPL/backtest?horizon=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["accuracy"], 0.5)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data", side_effect=RuntimeError("cache down"))
    @patch("ml.backtest.run_backtest", return_value={"accuracy": 0.5})
    @patch("ml.labels.build_labelled_frame", return_value=MagicMock())
    @patch("flow_api._ml_price_frame", return_value=MagicMock())
    def test_backtest_survives_cache_write_failure(
        self, _mock_frame, _mock_labels, _mock_backtest, _mock_set, _mock_get
    ):
        response = self.client.get("/api/predict/AAPL/backtest?horizon=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["accuracy"], 0.5)

    @patch("flow_api._ml_price_frame", side_effect=RuntimeError("bad frame"))
    def test_backtest_unexpected_error_returns_500(self, _mock_frame):
        response = self.client.get("/api/predict/AAPL/backtest")
        self.assertEqual(response.status_code, 500)

    @patch("flow_api._explore_cache_get", return_value={"cached": True})
    def test_explore_returns_cached_result(self, _mock_cache):
        response = self.client.get("/api/predict/AAPL/explore")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cached"], True)

    @patch("ml.dataset.payload_to_frame", return_value=None)
    @patch("flow_api.get_ml_price_history_payload", return_value={"data": []})
    def test_explore_insufficient_history_returns_422(self, _mock_hist, _mock_frame):
        response = self.client.get("/api/predict/AAPL/explore")
        self.assertEqual(response.status_code, 422)

    @patch("ml.explore.explore", side_effect=ValueError("bad knobs"))
    @patch("ml.dataset.payload_to_frame", return_value=[0] * 200)
    @patch("flow_api.get_ml_price_history_payload", return_value={"data": []})
    def test_explore_value_error_returns_422(
        self, _mock_hist, _mock_frame, _mock_explore
    ):
        response = self.client.get("/api/predict/AAPL/explore")
        self.assertEqual(response.status_code, 422)

    @patch("ml.explore.explore", side_effect=RuntimeError("boom"))
    @patch("ml.dataset.payload_to_frame", return_value=[0] * 200)
    @patch("flow_api.get_ml_price_history_payload", return_value={"data": []})
    def test_explore_unexpected_error_returns_500(
        self, _mock_hist, _mock_frame, _mock_explore
    ):
        response = self.client.get("/api/predict/AAPL/explore")
        self.assertEqual(response.status_code, 500)

    @patch("flow_api._ml_price_frame", side_effect=RuntimeError("bad frame"))
    def test_features_unexpected_error_returns_500(self, _mock_frame):
        response = self.client.get("/api/predict/AAPL/features")
        self.assertEqual(response.status_code, 500)


class TestPriceHistoryEndpointBranches(unittest.TestCase):
    """Cover date filtering and error handling on price history."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("flow_api.get_price_history_payload")
    def test_start_and_end_filter_rows(self, mock_payload):
        mock_payload.return_value = {
            "data": [
                {"Date": "2024-01-01", "Close": 100.0},
                {"Date": "2024-02-01", "Close": 101.0},
                {"Date": "2024-03-01", "Close": 102.0},
            ]
        }
        response = self.client.get(
            "/api/price-history/AAPL?start=2024-01-15&end=2024-02-15"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"], [{"Date": "2024-02-01", "Close": 101.0}]
        )

    @patch("flow_api.get_price_history_payload", side_effect=RuntimeError("boom"))
    def test_price_history_error_returns_500(self, _mock_payload):
        response = self.client.get("/api/price-history/AAPL")
        self.assertEqual(response.status_code, 500)


class TestDataEndpointErrorBranches(unittest.TestCase):
    """Cover generic 500 handlers on data endpoints."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    def test_data_endpoint_errors_return_500(self):
        cases = [
            ("/api/analyst-targets/AAPL", "flow.get_analyst_price_targets"),
            ("/api/calendar/AAPL", "flow.get_calendar"),
            ("/api/balance-sheet/AAPL", "flow.get_balance_sheet"),
            ("/api/income-stmt/AAPL", "flow.get_quarterly_income_stmt"),
            ("/api/news/AAPL", "flow.get_news"),
            ("/api/option-chain/AAPL", "flow.get_option_chain"),
            ("/api/recommendations/AAPL", "flow.get_recommendations"),
            ("/api/institutional-holders/AAPL", "flow.get_institutional_holders"),
            ("/api/insider-transactions/AAPL", "flow.get_insider_transactions"),
            ("/api/analyst-upgrades/AAPL", "flow.get_analyst_upgrades_downgrades"),
            ("/api/related-stocks/AAPL", "flow_api.get_related_stocks_payload"),
            ("/api/trading-strategy/AAPL", "flow.get_trading_strategy"),
            ("/api/decision-engine/AAPL", "flow_api.get_decision_engine_payload"),
        ]
        for path, target in cases:
            with self.subTest(path=path):
                with (
                    patch("db.get_cached_data", return_value=None),
                    patch("db.set_cached_data"),
                    patch(target, side_effect=RuntimeError("boom")),
                ):
                    response = self.client.get(path)
                self.assertEqual(response.status_code, 500)


class TestCacheEndpointBranches(unittest.TestCase):
    """Cover cache management success and failure paths."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("db.get_cache_stats")
    def test_cache_stats_success(self, mock_stats):
        mock_stats.return_value = {"entries": 2}
        response = self.client.get("/api/cache/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"entries": 2})

    @patch("db.get_cache_stats", side_effect=RuntimeError("boom"))
    def test_cache_stats_error(self, _mock_stats):
        response = self.client.get("/api/cache/stats")
        self.assertEqual(response.status_code, 500)

    @patch("db.clear_symbol_cache")
    def test_clear_symbol_cache_success(self, mock_clear):
        mock_clear.return_value = 4
        response = self.client.delete("/api/cache/AAPL")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted_entries"], 4)

    @patch("db.clear_symbol_cache", side_effect=RuntimeError("boom"))
    def test_clear_symbol_cache_error(self, _mock_clear):
        response = self.client.delete("/api/cache/AAPL")
        self.assertEqual(response.status_code, 500)

    @patch("db.clear_expired_cache")
    def test_clear_expired_cache_success(self, mock_clear):
        mock_clear.return_value = 3
        response = flow_api.clear_expired_cache()
        self.assertEqual(response.status_code, 200)

    @patch("db.clear_expired_cache", side_effect=RuntimeError("boom"))
    def test_clear_expired_cache_error(self, _mock_clear):
        with self.assertRaises(flow_api.HTTPException) as ctx:
            flow_api.clear_expired_cache()
        self.assertEqual(ctx.exception.status_code, 500)


class TestAiEndpointErrorBranches(unittest.TestCase):
    """Cover unexpected 500 paths on AI and Ollama-backed endpoints."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    def test_ai_endpoint_errors_return_500(self):
        cases = [
            (
                "/api/ai/fundamental-analysis/AAPL",
                "flow.get_ai_fundamental_analysis",
            ),
            (
                "/api/ai/balance-sheet-analysis/AAPL",
                "flow.get_ai_balance_sheet_analysis",
            ),
            (
                "/api/ai/income-stmt-analysis/AAPL",
                "flow.get_ai_quarterly_income_stm_analysis",
            ),
            ("/api/ai/technical-analysis/AAPL", "flow.get_ai_technical_analysis"),
            (
                "/api/ai/action-recommendation/AAPL",
                "flow.get_ai_action_recommendation",
            ),
            (
                "/api/ai/action-recommendation-sentence/AAPL",
                "flow.get_ai_action_recommendation_sentence",
            ),
            (
                "/api/ai/action-recommendation-word/AAPL",
                "flow.get_ai_action_recommendation_single_word",
            ),
            ("/api/ai/full-report/AAPL", "flow.get_ai_full_report"),
        ]
        for path, target in cases:
            with self.subTest(path=path):
                with (
                    patch("db.get_cached_data", return_value=None),
                    patch("db.set_cached_data"),
                    patch("flow.ensure_ollama"),
                    patch(target, side_effect=RuntimeError("boom")),
                ):
                    response = self.client.get(path)
                self.assertEqual(response.status_code, 500)

    def test_news_sentiment_timeout_returns_504(self):
        executor = MagicMock()
        future = MagicMock()
        future.result.side_effect = concurrent.futures.TimeoutError()
        executor.submit.return_value = future
        with patch("concurrent.futures.ThreadPoolExecutor") as mock_pool:
            mock_pool.return_value.__enter__.return_value = executor
            response = self.client.get("/api/ai/news-sentiment/AAPL")
        self.assertEqual(response.status_code, 504)


class TestFundamentalScreenerBranches(unittest.TestCase):
    """Cover fallback knobs, extra filters and row serialization."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("db_timescale.get_conn")
    def test_invalid_knobs_and_row_serialization(self, mock_get_conn):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = [
            {
                "ticker": "AAPL",
                "fetched_at": datetime(2024, 1, 2, 3, 4, 5),
                "market_cap": float("nan"),
            }
        ]
        mock_get_conn.return_value = conn

        response = self.client.get(
            "/api/fundamentals-db?sort_by=unsupported&sort_dir=sideways&limit=0"
            "&min_roe=0.1&max_debt_to_equity=2.0"
        )

        self.assertEqual(response.status_code, 200)
        row = response.json()["results"][0]
        self.assertEqual(row["fetched_at"], "2024-01-02T03:04:05")
        self.assertIsNone(row["market_cap"])

    @patch("db_timescale.get_conn", side_effect=RuntimeError("db down"))
    def test_screener_error_returns_500(self, _mock_get_conn):
        response = self.client.get("/api/fundamentals-db")
        self.assertEqual(response.status_code, 500)


class TestDbStatsStaleRows(unittest.TestCase):
    """Cover serialization of stalest ticker rows."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("db_timescale.get_conn")
    def test_stale_ticker_dates_are_serialized(self, mock_get_conn):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.side_effect = [
            {
                "total_rows": 1,
                "tickers": 1,
                "most_recent_date": None,
                "oldest_date": None,
            },
            {"total_rows": 1, "tickers": 1, "last_fetched": None},
            {"total_rows": 1, "tickers": 1, "most_recent_date": None},
        ]
        cursor.fetchall.return_value = [
            {"ticker": "XYZ", "last_date": datetime(2023, 6, 1)}
        ]
        mock_get_conn.return_value = conn

        response = self.client.get("/api/db/stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["stalest_tickers"][0]["last_date"], "2023-06-01T00:00:00"
        )


class TestExportListBranches(unittest.TestCase):
    """Cover CSV export for list-shaped fundamentals and price history."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("flow_api.get_fundamentals_payload")
    def test_export_fundamentals_list(self, mock_payload):
        mock_payload.return_value = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
        response = self.client.get("/api/export/fundamentals/AAPL?format=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("MSFT", response.text)

    @patch("flow_api.get_price_history_payload")
    def test_export_price_history_list(self, mock_payload):
        mock_payload.return_value = [
            {"Date": "2024-01-01", "Close": 100.0},
            {"Date": "2024-01-02", "Close": 101.0},
        ]
        response = self.client.get("/api/export/price-history/AAPL?format=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("2024-01-02", response.text)


class TestConnectionManager(unittest.IsolatedAsyncioTestCase):
    """Cover websocket connection bookkeeping and broadcast failures."""

    async def test_connect_disconnect_and_broadcast(self):
        manager = flow_api.ConnectionManager()
        websocket = MagicMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()

        await manager.connect(websocket, "aapl")
        self.assertIn("AAPL", manager.active_connections)

        manager.disconnect(websocket, "AAPL")
        self.assertEqual(manager.active_connections["AAPL"], [])

        manager.disconnect(websocket, "MISSING")

        good = MagicMock()
        good.send_text = AsyncMock()
        bad = MagicMock()
        bad.send_text = AsyncMock(side_effect=RuntimeError("closed"))
        manager.active_connections["AAPL"] = [good, bad]
        await manager.broadcast("aapl", "hello")
        good.send_text.assert_awaited_once_with("hello")

    async def test_connect_existing_symbol_appends(self):
        manager = flow_api.ConnectionManager()
        first = MagicMock()
        first.accept = AsyncMock()
        second = MagicMock()
        second.accept = AsyncMock()
        await manager.connect(first, "AAPL")
        await manager.connect(second, "AAPL")
        self.assertEqual(manager.active_connections["AAPL"], [first, second])


class TestPriceWebSocket(unittest.TestCase):
    """Cover the demonstration price websocket endpoint."""

    def test_ping_pong_and_disconnect(self):
        with (
            TestClient(flow_api.app) as client,
            client.websocket_connect("/ws/prices/aapl") as websocket,
        ):
            websocket.send_text("ping")
            self.assertEqual(websocket.receive_text(), "pong")


if __name__ == "__main__":
    unittest.main()
