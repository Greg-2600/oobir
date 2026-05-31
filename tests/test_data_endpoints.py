"""Unit tests for data endpoints."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestDataEndpoints(unittest.TestCase):
    """Test cases for data retrieval endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch("db.get_cached_data")
    @patch("db.set_cached_data")
    def mock_db(self, mock_set_cache, mock_get_cache):
        """Mock database caching to return None (cache miss)."""
        mock_get_cache.return_value = None
        return mock_set_cache, mock_get_cache

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())

    @patch("requests.get")
    def test_ollama_health_endpoint(self, mock_requests_get):
        """Test Ollama health check endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        response = self.client.get("/health/ollama")

        self.assertEqual(response.status_code, 200)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_fundamentals")
    def test_fundamentals_endpoint(
        self, mock_get_fundamentals, mock_set_cache, mock_get_cache
    ):
        """Test fundamentals endpoint."""
        mock_get_fundamentals.return_value = (
            '{"symbol": "AAPL", "pe_ratio": 25.5, "market_cap": 3000000000000}'
        )

        response = self.client.get("/api/fundamentals/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_fundamentals")
    def test_fundamentals_endpoint_error(
        self, mock_get_fundamentals, mock_set_cache, mock_get_cache
    ):
        """Test fundamentals endpoint error handling."""
        mock_get_fundamentals.side_effect = Exception("API Error")

        response = self.client.get("/api/fundamentals/INVALID")

        self.assertEqual(response.status_code, 500)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_price_history")
    def test_price_history_endpoint(
        self, mock_get_price_history, mock_set_cache, mock_get_cache
    ):
        """Test price history endpoint."""
        mock_get_price_history.return_value = [
            {"date": "2024-01-01", "close": 150.0},
            {"date": "2024-01-02", "close": 152.0},
        ]

        response = self.client.get("/api/price-history/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data, (list, dict)))
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_analyst_price_targets")
    def test_analyst_targets_endpoint(
        self, mock_get_analyst_targets, mock_set_cache, mock_get_cache
    ):
        """Test analyst targets endpoint."""
        mock_get_analyst_targets.return_value = {
            "symbol": "AAPL",
            "target_high": 200.0,
            "target_low": 150.0,
            "target_mean": 175.0,
        }

        response = self.client.get("/api/analyst-targets/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_calendar")
    def test_calendar_endpoint(self, mock_get_calendar, mock_set_cache, mock_get_cache):
        """Test calendar endpoint."""
        mock_get_calendar.return_value = [{"event": "Earnings", "date": "2024-01-25"}]

        response = self.client.get("/api/calendar/AAPL")

        self.assertEqual(response.status_code, 200)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_quarterly_income_stmt")
    def test_income_stmt_endpoint(
        self, mock_get_income_statement, mock_set_cache, mock_get_cache
    ):
        """Test income statement endpoint."""
        mock_get_income_statement.return_value = {
            "symbol": "AAPL",
            "revenue": 383285000000,
            "net_income": 96995000000,
        }

        response = self.client.get("/api/income-stmt/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_balance_sheet")
    def test_balance_sheet_endpoint(
        self, mock_get_balance_sheet, mock_set_cache, mock_get_cache
    ):
        """Test balance sheet endpoint."""
        mock_get_balance_sheet.return_value = {
            "symbol": "AAPL",
            "total_assets": 352755000000,
            "total_liabilities": 120715000000,
        }

        response = self.client.get("/api/balance-sheet/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_option_chain")
    def test_option_chain_endpoint(
        self, mock_get_option_chain, mock_set_cache, mock_get_cache
    ):
        """Test option chain endpoint."""
        mock_get_option_chain.return_value = {"symbol": "AAPL", "calls": [], "puts": []}

        response = self.client.get("/api/option-chain/AAPL")

        self.assertEqual(response.status_code, 200)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_news")
    def test_news_endpoint(self, mock_get_news, mock_set_cache, mock_get_cache):
        """Test news endpoint."""
        mock_get_news.return_value = [
            {
                "title": "Apple News",
                "source": "Reuters",
                "published": "2024-01-01T10:00:00Z",
            }
        ]

        response = self.client.get("/api/news/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_screen_undervalued_large_caps")
    def test_screen_undervalued_endpoint(
        self, mock_screen_undervalued, mock_set_cache, mock_get_cache
    ):
        """Test screen undervalued endpoint."""
        mock_screen_undervalued.return_value = ["AAPL", "MSFT", "GOOGL"]

        response = self.client.get("/api/screen-undervalued")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_screen_undervalued_large_caps")
    def test_screen_undervalued_endpoint_error(
        self, mock_screen_undervalued, mock_set_cache, mock_get_cache
    ):
        """Test screen undervalued endpoint error handling."""
        mock_screen_undervalued.side_effect = Exception("Screening failed")

        response = self.client.get("/api/screen-undervalued")

        self.assertEqual(response.status_code, 500)

    @patch("db_timescale.get_conn")
    @patch("db_timescale.list_fundamental_tickers")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_related_stocks_endpoint_returns_ranked_results(
        self, mock_fetch_fundamentals, mock_list_tickers, mock_get_conn
    ):
        """Test related stocks endpoint returns similarity-ranked related symbols."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        mock_list_tickers.return_value = ["TSLA", "RIVN", "NIO", "F", "GM"]

        fundamentals_map = {
            "TSLA": {
                "raw_info": {
                    "symbol": "TSLA",
                    "shortName": "Tesla, Inc.",
                    "currentPrice": 180.0,
                    "regularMarketPreviousClose": 176.0,
                    "averageVolume": 100000000,
                    "dividendYield": 0.0,
                }
            },
            "RIVN": {
                "raw_info": {
                    "symbol": "RIVN",
                    "shortName": "Rivian Automotive",
                    "currentPrice": 17.0,
                    "regularMarketPreviousClose": 16.6,
                    "averageVolume": 34000000,
                    "dividendYield": 0.0,
                }
            },
            "NIO": {
                "raw_info": {
                    "symbol": "NIO",
                    "shortName": "NIO Inc",
                    "currentPrice": 6.2,
                    "regularMarketPreviousClose": 6.0,
                    "averageVolume": 41000000,
                    "dividendYield": 0.0,
                }
            },
            "F": {
                "raw_info": {
                    "symbol": "F",
                    "shortName": "Ford Motor Company",
                    "currentPrice": 12.1,
                    "regularMarketPreviousClose": 11.9,
                    "averageVolume": 50000000,
                    "dividendYield": 0.052,
                }
            },
            "GM": {
                "raw_info": {
                    "symbol": "GM",
                    "shortName": "General Motors",
                    "currentPrice": 42.0,
                    "regularMarketPreviousClose": 41.8,
                    "averageVolume": 18000000,
                    "dividendYield": 0.009,
                }
            },
        }

        def _fetch_side_effect(_conn, ticker):
            return fundamentals_map.get(ticker)

        mock_fetch_fundamentals.side_effect = _fetch_side_effect

        response = self.client.get("/api/related-stocks/TSLA?limit=3")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("related", data)
        self.assertEqual(data["symbol"], "TSLA")
        self.assertEqual(len(data["related"]), 3)
        self.assertTrue(all("ticker" in item for item in data["related"]))
        self.assertTrue(all("link" in item for item in data["related"]))
        self.assertNotIn("TSLA", [item["ticker"] for item in data["related"]])

        mock_conn.close.assert_called_once()

    @patch("db_timescale.get_conn")
    @patch("db_timescale.list_fundamental_tickers")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_related_stocks_respects_exclude_list(
        self, mock_fetch_fundamentals, mock_list_tickers, mock_get_conn
    ):
        """Test related stocks endpoint does not return explicitly excluded symbols."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        mock_list_tickers.return_value = ["TSLA", "RIVN", "NIO", "F"]

        fundamentals = {
            "raw_info": {
                "symbol": "X",
                "shortName": "Test",
                "currentPrice": 100.0,
                "regularMarketPreviousClose": 99.0,
                "averageVolume": 20000000,
                "dividendYield": 0.0,
            }
        }
        mock_fetch_fundamentals.return_value = fundamentals

        response = self.client.get("/api/related-stocks/TSLA?limit=3&exclude=RIVN,NIO")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        tickers = [item["ticker"] for item in data["related"]]
        self.assertNotIn("RIVN", tickers)
        self.assertNotIn("NIO", tickers)


if __name__ == "__main__":
    unittest.main()
