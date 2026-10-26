"""Tests for /api/stock-snapshot and /api/screen-undervalued endpoints."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import flow_api


class TestStockSnapshotEndpoint(unittest.TestCase):
    """Tests for the /api/stock-snapshot/{symbol} endpoint."""

    def setUp(self):
        self.client = TestClient(flow_api.app)
        self.symbol = "AAPL"

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_related_stocks_payload")
    @patch("flow_api.get_decision_engine_payload")
    @patch("flow_api.with_cache")
    def test_snapshot_returns_all_sections(
        self, mock_cache, mock_related, mock_decision, mock_price, mock_fund
    ):
        mock_fund.return_value = {"ticker": "AAPL", "marketCap": 3000000000000}
        mock_price.return_value = {
            "data": [
                {
                    "Date": "2024-01-01",
                    "Close": 150.0,
                    "Open": 149.0,
                    "High": 151.0,
                    "Low": 148.0,
                    "Volume": 1000000,
                }
            ]
        }
        mock_related.return_value = []
        mock_decision.return_value = {
            "symbol": "AAPL",
            "action": "WAIT",
            "score": 0.0,
        }
        mock_cache.return_value = None

        resp = self.client.get(f"/api/stock-snapshot/{self.symbol}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["symbol"], "AAPL")
        self.assertIn("fundamentals", data)
        self.assertIn("price_history", data)
        self.assertIn("news", data)
        self.assertIn("analyst_targets", data)
        self.assertIn("calendar", data)
        self.assertIn("option_chain", data)
        self.assertIn("related_stocks", data)
        self.assertIn("decision_engine", data)
        self.assertIn("section_errors", data)

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_related_stocks_payload")
    @patch("flow_api.get_decision_engine_payload")
    @patch("flow_api.with_cache")
    def test_snapshot_handles_section_error(
        self, mock_cache, mock_related, mock_decision, mock_price, mock_fund
    ):
        mock_fund.side_effect = Exception("Fundamentals unavailable")
        mock_price.return_value = {"data": []}
        mock_related.return_value = []
        mock_decision.return_value = {"symbol": "AAPL", "action": "WAIT"}
        mock_cache.return_value = None

        resp = self.client.get(f"/api/stock-snapshot/{self.symbol}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("section_errors", data)
        self.assertIn("fundamentals", data["section_errors"])

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_related_stocks_payload")
    @patch("flow_api.get_decision_engine_payload")
    @patch("flow_api.with_cache")
    def test_snapshot_portfolio_tickers_parsed(
        self, mock_cache, mock_related, mock_decision, mock_price, mock_fund
    ):
        mock_fund.return_value = {"ticker": "AAPL"}
        mock_price.return_value = {
            "data": [
                {
                    "Date": "2024-01-01",
                    "Close": 150.0,
                    "Open": 149.0,
                    "High": 151.0,
                    "Low": 148.0,
                    "Volume": 1000000,
                }
            ]
        }
        mock_related.return_value = []
        mock_decision.return_value = {"symbol": "AAPL", "action": "WAIT"}
        mock_cache.return_value = None

        resp = self.client.get(
            f"/api/stock-snapshot/{self.symbol}?portfolio=MSFT,GOOGL"
        )
        self.assertEqual(resp.status_code, 200)

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_related_stocks_payload")
    @patch("flow_api.get_decision_engine_payload")
    @patch("flow_api.with_cache")
    def test_snapshot_related_limit_param(
        self, mock_cache, mock_related, mock_decision, mock_price, mock_fund
    ):
        mock_fund.return_value = {"ticker": "AAPL"}
        mock_price.return_value = {
            "data": [
                {
                    "Date": "2024-01-01",
                    "Close": 150.0,
                    "Open": 149.0,
                    "High": 151.0,
                    "Low": 148.0,
                    "Volume": 1000000,
                }
            ]
        }
        mock_related.return_value = []
        mock_decision.return_value = {"symbol": "AAPL", "action": "WAIT"}
        mock_cache.return_value = None

        resp = self.client.get(f"/api/stock-snapshot/{self.symbol}?related_limit=5")
        self.assertEqual(resp.status_code, 200)

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_related_stocks_payload")
    @patch("flow_api.get_decision_engine_payload")
    @patch("flow_api.with_cache")
    def test_snapshot_exclude_param(
        self, mock_cache, mock_related, mock_decision, mock_price, mock_fund
    ):
        mock_fund.return_value = {"ticker": "AAPL"}
        mock_price.return_value = {
            "data": [
                {
                    "Date": "2024-01-01",
                    "Close": 150.0,
                    "Open": 149.0,
                    "High": 151.0,
                    "Low": 148.0,
                    "Volume": 1000000,
                }
            ]
        }
        mock_related.return_value = []
        mock_decision.return_value = {"symbol": "AAPL", "action": "WAIT"}
        mock_cache.return_value = None

        resp = self.client.get(f"/api/stock-snapshot/{self.symbol}?exclude=MSFT,GOOGL")
        self.assertEqual(resp.status_code, 200)

    def test_snapshot_symbol_uppercased(self):
        with patch("flow_api.get_fundamentals_payload") as mock_fund, patch(
            "flow_api.get_price_history_payload"
        ) as mock_price, patch(
            "flow_api.get_related_stocks_payload"
        ) as mock_related, patch(
            "flow_api.get_decision_engine_payload"
        ) as mock_decision, patch(
            "flow_api.with_cache"
        ) as mock_cache:
            mock_fund.return_value = {"ticker": "AAPL"}
            mock_price.return_value = {"data": []}
            mock_related.return_value = []
            mock_decision.return_value = {"symbol": "AAPL", "action": "WAIT"}
            mock_cache.return_value = None

            resp = self.client.get("/api/stock-snapshot/aapl")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["symbol"], "AAPL")


class TestScreenUndervaluedEndpoint(unittest.TestCase):
    """Tests for the /api/screen-undervalued endpoint."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    @patch("flow_api.flow.get_screen_undervalued_large_caps")
    @patch("flow_api.db.get_cached_data")
    @patch("flow_api.db.set_cached_data")
    def test_screen_returns_cached(self, mock_set, mock_get, mock_screen):
        mock_get.return_value = {"screen": "cached_result", "tickers": ["AAPL"]}

        resp = self.client.get("/api/screen-undervalued")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["screen"], "cached_result")
        mock_screen.assert_not_called()

    @patch("flow_api.flow.get_screen_undervalued_large_caps")
    @patch("flow_api.db.get_cached_data")
    @patch("flow_api.db.set_cached_data")
    def test_screen_fetches_fresh_on_cache_miss(self, mock_set, mock_get, mock_screen):
        mock_get.return_value = None
        mock_screen.return_value = {"screen": "fresh_result", "tickers": ["MSFT"]}

        resp = self.client.get("/api/screen-undervalued")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["screen"], "fresh_result")
        mock_screen.assert_called_once()
        mock_set.assert_called_once()

    @patch("flow_api.flow.get_screen_undervalued_large_caps")
    @patch("flow_api.db.get_cached_data")
    def test_screen_handles_error(self, mock_get, mock_screen):
        mock_get.return_value = None
        mock_screen.side_effect = Exception("Screen computation failed")

        resp = self.client.get("/api/screen-undervalued")
        self.assertEqual(resp.status_code, 500)


class TestDecisionEnginePayload(unittest.TestCase):
    """Tests for the get_decision_engine_payload function."""

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    def test_decision_engine_basic(self, mock_price, mock_fund):
        from flow_api import get_decision_engine_payload

        mock_fund.return_value = {
            "currentPrice": 150.0,
            "trailingPE": 25.0,
            "dividendYield": 0.02,
            "returnOnEquity": 0.15,
            "sector": "Technology",
        }
        mock_price.return_value = {
            "data": [
                {
                    "Date": f"2024-01-{i:02d}",
                    "Close": 100.0 + i,
                    "Open": 99.0 + i,
                    "High": 101.0 + i,
                    "Low": 98.0 + i,
                    "Volume": 1000000,
                }
                for i in range(1, 60)
            ]
        }

        result = get_decision_engine_payload("AAPL")

        self.assertIn("symbol", result)
        self.assertIn("action", result)
        self.assertIn("score", result)
        self.assertIn("confidence", result)
        self.assertIn("risk_gates", result)
        self.assertIn("metrics", result)
        self.assertIn("component_scores", result)
        self.assertIn("reason_codes", result)

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    def test_decision_engine_consider_long_action(self, mock_price, mock_fund):
        from flow_api import get_decision_engine_payload

        mock_fund.return_value = {
            "currentPrice": 150.0,
            "trailingPE": 15.0,
            "dividendYield": 0.03,
            "returnOnEquity": 0.25,
            "sector": "Technology",
        }
        price_data = []
        for i in range(60):
            price_data.append(
                {
                    "Date": f"2024-01-{i+1:02d}",
                    "Close": 100.0 + i * 2,
                    "Open": 99.0 + i * 2,
                    "High": 102.0 + i * 2,
                    "Low": 98.0 + i * 2,
                    "Volume": 1000000,
                }
            )
        mock_price.return_value = {"data": price_data}

        result = get_decision_engine_payload("AAPL")

        self.assertIn(result["action"], ["CONSIDER_LONG", "WAIT", "REDUCE_RISK"])

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    def test_decision_engine_with_portfolio(self, mock_price, mock_fund):
        from flow_api import get_decision_engine_payload

        def fund_side_effect(symbol):
            if symbol == "AAPL":
                return {
                    "currentPrice": 150.0,
                    "trailingPE": 15.0,
                    "dividendYield": 0.03,
                    "returnOnEquity": 0.25,
                    "sector": "Technology",
                }
            elif symbol == "MSFT":
                return {
                    "currentPrice": 400.0,
                    "trailingPE": 30.0,
                    "dividendYield": 0.01,
                    "returnOnEquity": 0.20,
                    "sector": "Technology",
                }
            return {}

        def price_side_effect(symbol):
            return {
                "data": [
                    {
                        "Date": f"2024-01-{i:02d}",
                        "Close": 100.0 + i,
                        "Open": 99.0 + i,
                        "High": 101.0 + i,
                        "Low": 98.0 + i,
                        "Volume": 1000000,
                    }
                    for i in range(1, 60)
                ]
            }

        mock_fund.side_effect = fund_side_effect
        mock_price.side_effect = price_side_effect

        result = get_decision_engine_payload(
            "AAPL", portfolio_tickers=["MSFT", "GOOGL"]
        )

        self.assertIn("portfolio_adjustments", result)
        self.assertIn("tickers", result["portfolio_adjustments"])

    @patch("flow_api.get_fundamentals_payload")
    @patch("flow_api.get_price_history_payload")
    def test_decision_engine_empty_closes(self, mock_price, mock_fund):
        from flow_api import get_decision_engine_payload

        mock_fund.return_value = {
            "currentPrice": 150.0,
            "trailingPE": 25.0,
        }
        mock_price.return_value = {"data": []}

        result = get_decision_engine_payload("AAPL")

        self.assertEqual(result["metrics"]["data_points"], 0)
        self.assertTrue(result["risk_gates"]["weak_data"])


if __name__ == "__main__":
    unittest.main()
