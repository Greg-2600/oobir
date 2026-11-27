"""Focused coverage tests for the remaining data-route branches in flow_api."""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestTradingStrategyRoute(unittest.TestCase):
    """Exercise success, empty, cached and error paths of the data route."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value=None)
    @patch("flow.get_trading_strategy")
    def test_success_returns_payload(self, mock_strategy, _mock_get, mock_set):
        mock_strategy.return_value = {
            "symbol": "AAPL",
            "strategy": "buy-the-dip",
            "entry": 180.0,
        }

        response = self.client.get("/api/trading-strategy/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["strategy"], "buy-the-dip")
        mock_strategy.assert_called_once_with("AAPL")
        mock_set.assert_called_once()

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value=None)
    @patch("flow.get_trading_strategy", return_value={})
    def test_empty_payload_returns_empty_object(
        self, _mock_strategy, _mock_get, _mock_set
    ):
        response = self.client.get("/api/trading-strategy/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    @patch("db.get_cached_data", return_value={"symbol": "AAPL", "cached": True})
    @patch("flow.get_trading_strategy")
    def test_cached_payload_skips_fetch(self, mock_strategy, _mock_get):
        response = self.client.get("/api/trading-strategy/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["cached"])
        mock_strategy.assert_not_called()

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value=None)
    @patch("flow.get_trading_strategy", side_effect=RuntimeError("provider down"))
    def test_error_returns_500(self, _mock_strategy, _mock_get, _mock_set):
        response = self.client.get("/api/trading-strategy/AAPL")

        self.assertEqual(response.status_code, 500)
        self.assertIn("provider down", response.json()["detail"])


class TestDecisionEnginePortfolioBranches(unittest.TestCase):
    """Cover sector/correlation penalties, empty holdings and lookup errors."""

    def _payload(self, closes):
        return {"data": [{"Close": value} for value in closes]}

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_sector_overlap_and_high_correlation_penalties(self, mock_fund, mock_price):
        closes = [100.0 + idx for idx in range(60)]
        mock_fund.side_effect = lambda symbol: {
            "sector": "Technology",
            "trailingPE": 20.0,
            "returnOnEquity": 0.2,
        }
        mock_price.side_effect = lambda symbol: self._payload(closes)

        result = flow_api.get_decision_engine_payload("AAPL", ["MSFT", "GOOGL"])

        adjustments = result["portfolio_adjustments"]
        self.assertEqual(adjustments["sector_penalty"], 16.0)
        self.assertEqual(adjustments["correlation_penalty"], 25.0)
        self.assertTrue(any("Sector overlap" in note for note in result["risk_notes"]))
        self.assertTrue(
            any("High correlation" in note for note in result["risk_notes"])
        )

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_holding_lookup_error_is_skipped(self, mock_fund, mock_price):
        closes = [100.0 + idx for idx in range(60)]

        def fund_side_effect(symbol):
            if symbol == "BAD":
                raise RuntimeError("lookup failed")
            return {"sector": "Technology", "trailingPE": 20.0}

        mock_fund.side_effect = fund_side_effect
        mock_price.side_effect = lambda symbol: self._payload(closes)

        result = flow_api.get_decision_engine_payload("AAPL", ["BAD", "MSFT"])

        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["portfolio_adjustments"]["tickers"], ["BAD", "MSFT"])

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_empty_price_history_with_portfolio(self, mock_fund, mock_price):
        mock_fund.return_value = {"sector": "Technology"}
        mock_price.return_value = self._payload([])

        result = flow_api.get_decision_engine_payload("AAPL", ["MSFT"])

        self.assertEqual(result["metrics"]["data_points"], 0)
        self.assertTrue(result["risk_gates"]["weak_data"])

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_short_holding_history_skips_correlation(self, mock_fund, mock_price):
        mock_fund.return_value = {"sector": "Technology", "trailingPE": 20.0}

        def price_side_effect(symbol):
            if symbol == "MSFT":
                return self._payload([100.0, 101.0, 102.0, 103.0, 104.0])
            return self._payload([100.0 + idx for idx in range(60)])

        mock_price.side_effect = price_side_effect

        result = flow_api.get_decision_engine_payload("AAPL", ["MSFT"])

        self.assertEqual(result["portfolio_adjustments"]["correlation_penalty"], 0.0)

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_flat_holding_prices_skip_correlation(self, mock_fund, mock_price):
        mock_fund.return_value = {"sector": "Technology", "trailingPE": 20.0}

        def price_side_effect(symbol):
            if symbol == "MSFT":
                return self._payload([100.0] * 60)
            return self._payload([100.0 + idx for idx in range(60)])

        mock_price.side_effect = price_side_effect

        result = flow_api.get_decision_engine_payload("AAPL", ["MSFT"])

        self.assertEqual(result["portfolio_adjustments"]["correlation_penalty"], 0.0)

    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_missing_pe_ratio_leaves_valuation_neutral(self, mock_fund, mock_price):
        mock_fund.return_value = {"returnOnEquity": 0.0}
        mock_price.return_value = self._payload([100.0 + idx for idx in range(60)])

        result = flow_api.get_decision_engine_payload("AAPL")

        self.assertEqual(result["component_scores"]["valuation"], 0.0)


class TestPriceHistoryPayloadBranches(unittest.TestCase):
    """Cover normalization, cache trimming and DB/flow fallback branches."""

    def test_normalize_non_dict_payload_returns_unchanged(self):
        payload = None
        self.assertIs(flow_api.normalize_price_history_payload(payload), payload)

    def test_normalize_dict_without_data_returns_unchanged(self):
        payload = {"meta": "no-data"}
        self.assertIs(flow_api.normalize_price_history_payload(payload), payload)

    def test_normalize_dict_with_non_list_data_returns_unchanged(self):
        payload = {"data": "not-a-list"}
        self.assertIs(flow_api.normalize_price_history_payload(payload), payload)

    def test_normalize_list_trims_to_window(self):
        payload = list(range(flow_api.PRICE_HISTORY_WINDOW + 10))
        trimmed = flow_api.normalize_price_history_payload(payload)
        self.assertEqual(len(trimmed), flow_api.PRICE_HISTORY_WINDOW)
        self.assertEqual(trimmed[-1], payload[-1])

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value={"data": [{"Close": 1.0}]})
    def test_equal_cached_payload_is_not_rewritten(self, _mock_get, mock_set):
        result = flow_api.get_price_history_payload("AAPL")

        self.assertEqual(result, {"data": [{"Close": 1.0}]})
        mock_set.assert_not_called()

    @patch("db.set_cached_data")
    @patch("db.get_cached_data")
    def test_oversized_cached_payload_is_trimmed_and_rewritten(
        self, mock_get, mock_set
    ):
        cached = {
            "data": [
                {"Close": float(idx)}
                for idx in range(flow_api.PRICE_HISTORY_WINDOW + 5)
            ]
        }
        mock_get.return_value = cached

        result = flow_api.get_price_history_payload("AAPL")

        self.assertEqual(len(result["data"]), flow_api.PRICE_HISTORY_WINDOW)
        mock_set.assert_called_once_with("price-history", result, "AAPL")

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value=None)
    @patch("db_timescale.fetch_price_history")
    @patch("db_timescale.get_conn")
    def test_db_rows_are_used_before_flow_fallback(
        self, mock_get_conn, mock_fetch, _mock_get, mock_set
    ):
        conn = MagicMock()
        mock_get_conn.return_value = conn
        mock_fetch.return_value = [{"date": "2024-01-01", "close": 10.0}]

        result = flow_api.get_price_history_payload("AAPL")

        self.assertEqual(result["data"][0]["close"], 10.0)
        conn.close.assert_called_once()
        mock_set.assert_called_once()

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value=None)
    @patch("flow.get_price_history")
    @patch("db_timescale.get_conn", side_effect=RuntimeError("db down"))
    def test_db_failure_falls_back_to_flow_json_string(
        self, _mock_get_conn, mock_flow, _mock_get, mock_set
    ):
        mock_flow.return_value = json.dumps({"data": [{"Close": 12.5}]})

        result = flow_api.get_price_history_payload("AAPL")

        self.assertEqual(result["data"][0]["Close"], 12.5)
        mock_set.assert_called_once()

    def test_extract_close_series_without_rows_returns_empty(self):
        self.assertEqual(flow_api._extract_close_series(None), [])
        self.assertEqual(flow_api._extract_close_series("not-a-payload"), [])


class TestPriceHistoryEndpointFilterBranches(unittest.TestCase):
    """Cover single-sided date filters and non-list payloads."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    def _payload(self):
        return {
            "data": [
                {"Date": "2024-01-01", "Close": 100.0},
                {"Date": "2024-02-01", "Close": 101.0},
                {"Date": "2024-03-01", "Close": 102.0},
            ]
        }

    @patch("flow_api.get_price_history_payload")
    def test_start_only_filters_rows(self, mock_payload):
        mock_payload.return_value = self._payload()

        response = self.client.get("/api/price-history/AAPL?start=2024-02-01")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 2)
        self.assertEqual(response.json()["data"][0]["Date"], "2024-02-01")

    @patch("flow_api.get_price_history_payload")
    def test_end_only_filters_rows(self, mock_payload):
        mock_payload.return_value = self._payload()

        response = self.client.get("/api/price-history/AAPL?end=2024-02-01")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 2)
        self.assertEqual(response.json()["data"][-1]["Date"], "2024-02-01")

    @patch("flow_api.get_price_history_payload")
    def test_non_list_payload_is_returned_unchanged(self, mock_payload):
        mock_payload.return_value = {"meta": "no-data"}

        response = self.client.get("/api/price-history/AAPL?start=2024-02-01")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"meta": "no-data"})


class TestExportEmptyBranches(unittest.TestCase):
    """Cover CSV exports when the payload shape has no tabular rows."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("flow_api.get_price_history_payload", return_value={"data": []})
    def test_export_price_history_csv_empty_rows(self, _mock_payload):
        response = self.client.get("/api/export/price-history/AAPL?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")

    @patch("flow_api.get_price_history_payload", return_value={"data": "not-a-list"})
    def test_export_price_history_csv_non_list_rows(self, _mock_payload):
        response = self.client.get("/api/export/price-history/AAPL?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")

    @patch("flow_api.get_price_history_payload", return_value="not-tabular")
    def test_export_price_history_csv_plain_value(self, _mock_payload):
        response = self.client.get("/api/export/price-history/AAPL?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")

    @patch("flow_api.get_fundamentals_payload", return_value="not-tabular")
    def test_export_fundamentals_csv_plain_value(self, _mock_payload):
        response = self.client.get("/api/export/fundamentals/AAPL?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")


class TestFundamentalsPayloadBranches(unittest.TestCase):
    """Cover DB payloads that already carry symbol and legacy aliases."""

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value=None)
    @patch("db_timescale.fetch_latest_fundamentals")
    @patch("db_timescale.get_conn")
    def test_existing_symbol_and_aliases_are_preserved(
        self, mock_get_conn, mock_fetch, _mock_get, mock_set
    ):
        conn = MagicMock()
        mock_get_conn.return_value = conn
        mock_fetch.return_value = {
            "raw_info": {
                "symbol": "AAPL",
                "trailingPE": 20.0,
                "marketCap": 1000.0,
                "pe_ratio": 20.0,
                "market_cap": 1000.0,
            }
        }

        result = flow_api.get_fundamentals_payload("AAPL")

        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["pe_ratio"], 20.0)
        self.assertEqual(result["market_cap"], 1000.0)
        conn.close.assert_called_once()
        mock_set.assert_called_once()

    @patch("db.set_cached_data")
    @patch("db.get_cached_data", return_value=None)
    @patch("db_timescale.fetch_latest_fundamentals", return_value=["not-a-dict"])
    @patch("db_timescale.get_conn")
    def test_non_dict_db_payload_is_serialized(
        self, mock_get_conn, _mock_fetch, _mock_get, mock_set
    ):
        conn = MagicMock()
        mock_get_conn.return_value = conn

        result = flow_api.get_fundamentals_payload("AAPL")

        self.assertEqual(result, ["not-a-dict"])
        conn.close.assert_called_once()
        mock_set.assert_called_once()


class TestFundamentalsDbScreenerBranches(unittest.TestCase):
    """Cover the screener query without optional filters."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("db_timescale.get_conn")
    def test_no_filters_returns_empty_results(self, mock_get_conn):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = []
        mock_get_conn.return_value = conn

        response = self.client.get("/api/fundamentals-db")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "results": []})
        conn.close.assert_called_once()


class TestSerializeValueFallback(unittest.TestCase):
    """Cover the pass-through branch used when serializing data payloads."""

    def test_unknown_object_is_returned_unchanged(self):
        value = object()
        self.assertIs(flow_api.serialize_value(value), value)


if __name__ == "__main__":
    unittest.main()
