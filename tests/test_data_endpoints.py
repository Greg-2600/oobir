"""Unit tests for data endpoints."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

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
    @patch("flow.get_recommendations")
    def test_recommendations_endpoint(
        self, mock_get_recommendations, mock_set_cache, mock_get_cache
    ):
        """Test analyst recommendations endpoint."""
        mock_get_recommendations.return_value = {
            "period": ["0m", "-1m"],
            "strongBuy": [6, 6],
            "buy": [18, 19],
            "hold": [14, 13],
            "sell": [3, 3],
            "strongSell": [3, 2],
        }

        response = self.client.get("/api/recommendations/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("period", data)
        self.assertIn("strongBuy", data)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_recommendations")
    def test_recommendations_not_found(
        self, mock_get_recommendations, mock_set_cache, mock_get_cache
    ):
        """Test recommendations returns 404 when no data."""
        mock_get_recommendations.return_value = None

        response = self.client.get("/api/recommendations/INVALID")

        self.assertEqual(response.status_code, 404)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_institutional_holders")
    def test_institutional_holders_endpoint(
        self, mock_get_inst_holders, mock_set_cache, mock_get_cache
    ):
        """Test institutional holders endpoint."""
        mock_get_inst_holders.return_value = {
            "Holder": ["Blackrock Inc.", "Vanguard"],
            "pctHeld": [0.0797, 0.0657],
            "Shares": [1162996939, 959107911],
        }

        response = self.client.get("/api/institutional-holders/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Holder", data)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_institutional_holders")
    def test_institutional_holders_not_found(
        self, mock_get_inst_holders, mock_set_cache, mock_get_cache
    ):
        """Test institutional holders returns 404 when no data."""
        mock_get_inst_holders.return_value = None

        response = self.client.get("/api/institutional-holders/INVALID")

        self.assertEqual(response.status_code, 404)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_insider_transactions")
    def test_insider_transactions_endpoint(
        self, mock_get_insider, mock_set_cache, mock_get_cache
    ):
        """Test insider transactions endpoint."""
        mock_get_insider.return_value = {
            "Insider": ["NEWSTEAD JENNIFER"],
            "Shares": [2399],
            "Value": [814748.0],
            "Transaction": ["Sale"],
        }

        response = self.client.get("/api/insider-transactions/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Insider", data)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_insider_transactions")
    def test_insider_transactions_not_found(
        self, mock_get_insider, mock_set_cache, mock_get_cache
    ):
        """Test insider transactions returns 404 when no data."""
        mock_get_insider.return_value = None

        response = self.client.get("/api/insider-transactions/INVALID")

        self.assertEqual(response.status_code, 404)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_analyst_upgrades_downgrades")
    def test_analyst_upgrades_endpoint(
        self, mock_get_upgrades, mock_set_cache, mock_get_cache
    ):
        """Test analyst upgrades/downgrades endpoint."""
        mock_get_upgrades.return_value = {
            "Firm": ["MoffettNathanson", "Loop Capital"],
            "ToGrade": ["Neutral", "Hold"],
            "FromGrade": ["Neutral", "Buy"],
            "Action": ["main", "down"],
        }

        response = self.client.get("/api/analyst-upgrades/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Firm", data)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.get_analyst_upgrades_downgrades")
    def test_analyst_upgrades_not_found(
        self, mock_get_upgrades, mock_set_cache, mock_get_cache
    ):
        """Test analyst upgrades returns 404 when no data."""
        mock_get_upgrades.return_value = None

        response = self.client.get("/api/analyst-upgrades/INVALID")

        self.assertEqual(response.status_code, 404)

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

    @patch("flow_api.get_related_stocks_payload")
    @patch("flow_api.get_decision_engine_payload")
    @patch("flow_api.with_cache")
    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_stock_snapshot_endpoint_returns_all_sections(
        self,
        mock_get_fundamentals_payload,
        mock_get_price_history_payload,
        mock_with_cache,
        mock_get_decision_engine_payload,
        mock_get_related_stocks_payload,
    ):
        """Test aggregated snapshot endpoint returns primary section payloads."""
        mock_get_fundamentals_payload.return_value = {
            "symbol": "AAPL",
            "pe_ratio": 25.5,
        }
        mock_get_price_history_payload.return_value = {
            "data": [{"Date": "2024-01-01", "Close": 150.0}]
        }
        mock_with_cache.side_effect = [
            [{"title": "Apple News"}],
            {"target_mean": 180.0},
            [{"event": "Earnings"}],
            {"calls": [], "puts": []},
        ]
        mock_get_related_stocks_payload.return_value = {
            "symbol": "AAPL",
            "related": [{"ticker": "MSFT", "link": "index.html?ticker=MSFT"}],
        }
        mock_get_decision_engine_payload.return_value = {
            "symbol": "AAPL",
            "action": "CONSIDER_LONG",
            "score": 42.0,
            "confidence": 0.74,
        }

        response = self.client.get(
            "/api/stock-snapshot/AAPL?related_limit=3&exclude=MSFT&portfolio=MSFT,NVDA,AAPL"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        self.assertIn("fundamentals", data)
        self.assertIn("price_history", data)
        self.assertIn("related_stocks", data)
        self.assertIn("decision_engine", data)
        self.assertEqual(data["section_errors"], {})
        mock_get_decision_engine_payload.assert_called_with("AAPL", ["MSFT", "NVDA"])

    @patch("flow_api.get_related_stocks_payload")
    @patch("flow_api.get_decision_engine_payload")
    @patch("flow_api.with_cache")
    @patch("flow_api.get_price_history_payload")
    @patch("flow_api.get_fundamentals_payload")
    def test_stock_snapshot_endpoint_records_section_errors(
        self,
        mock_get_fundamentals_payload,
        mock_get_price_history_payload,
        mock_with_cache,
        mock_get_decision_engine_payload,
        mock_get_related_stocks_payload,
    ):
        """Test snapshot endpoint returns partial data with section-level errors."""
        mock_get_fundamentals_payload.side_effect = Exception("fundamentals failed")
        mock_get_price_history_payload.return_value = {"data": []}
        mock_with_cache.side_effect = [{}, {}, {}, {}]
        mock_get_related_stocks_payload.return_value = {"symbol": "AAPL", "related": []}
        mock_get_decision_engine_payload.side_effect = Exception("decision failed")

        response = self.client.get("/api/stock-snapshot/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["fundamentals"])
        self.assertIn("fundamentals", data["section_errors"])
        self.assertIn("decision_engine", data["section_errors"])
        mock_get_decision_engine_payload.assert_called_with("AAPL", [])

    @patch("flow_api.get_decision_engine_payload")
    def test_decision_engine_endpoint_returns_payload(self, mock_get_decision_engine):
        """Decision engine endpoint should expose deterministic score payload."""
        mock_get_decision_engine.return_value = {
            "symbol": "AAPL",
            "action": "WAIT",
            "score": 11.5,
            "confidence": 0.58,
            "risk_gates": {"weak_data": False},
            "reason_codes": ["MOMENTUM_POSITIVE"],
        }

        response = self.client.get("/api/decision-engine/AAPL?portfolio=MSFT,NVDA,AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        self.assertIn("score", data)
        self.assertIn("confidence", data)
        mock_get_decision_engine.assert_called_with("AAPL", ["MSFT", "NVDA"])

    @patch("db_timescale.get_conn")
    @patch("db_timescale.list_fundamental_tickers")
    @patch("db_timescale.fetch_latest_fundamentals_bulk")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_related_stocks_endpoint_returns_ranked_results(
        self,
        mock_fetch_fundamentals,
        mock_fetch_fundamentals_bulk,
        mock_list_tickers,
        mock_get_conn,
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

        mock_fetch_fundamentals.return_value = fundamentals_map["TSLA"]
        mock_fetch_fundamentals_bulk.return_value = {
            ticker: fundamentals_map[ticker] for ticker in ["RIVN", "NIO", "F", "GM"]
        }

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
    @patch("db_timescale.fetch_latest_fundamentals_bulk")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_related_stocks_respects_exclude_list(
        self,
        mock_fetch_fundamentals,
        mock_fetch_fundamentals_bulk,
        mock_list_tickers,
        mock_get_conn,
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
        mock_fetch_fundamentals_bulk.return_value = {
            "RIVN": fundamentals,
            "NIO": fundamentals,
            "F": fundamentals,
        }

        response = self.client.get("/api/related-stocks/TSLA?limit=3&exclude=RIVN,NIO")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        tickers = [item["ticker"] for item in data["related"]]
        self.assertNotIn("RIVN", tickers)
        self.assertNotIn("NIO", tickers)

    @patch("db_timescale.get_conn")
    def test_fundamentals_db_sectors(self, mock_get_conn):
        """Test sectors endpoint returns distinct sectors from DB."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [
            ("Technology",),
            ("Healthcare",),
            ("Financial Services",),
        ]
        mock_get_conn.return_value = mock_conn

        response = self.client.get("/api/fundamentals-db/sectors")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sectors", data)
        self.assertEqual(
            data["sectors"], ["Technology", "Healthcare", "Financial Services"]
        )
        mock_conn.close.assert_called_once()

    @patch("db_timescale.get_conn")
    def test_fundamentals_db_sectors_error(self, mock_get_conn):
        """Test sectors endpoint returns 500 on DB error."""
        mock_get_conn.side_effect = Exception("DB connection failed")

        response = self.client.get("/api/fundamentals-db/sectors")

        self.assertEqual(response.status_code, 500)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.get_conn")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_fundamentals_db_endpoint(
        self, mock_fetch, mock_get_conn, mock_set_cache, mock_get_cache
    ):
        """Test fundamentals-db endpoint returns stored fundamentals."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_fetch.return_value = {
            "ticker": "AAPL",
            "short_name": "Apple Inc.",
            "sector": "Technology",
            "market_cap": 3000000000000,
            "trailing_pe": 25.5,
        }

        response = self.client.get("/api/fundamentals-db/AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ticker"], "AAPL")
        self.assertIn("market_cap", data)
        mock_conn.close.assert_called_once()

    @patch("db_timescale.get_conn")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_fundamentals_db_not_found(self, mock_fetch, mock_get_conn):
        """Test fundamentals-db endpoint returns 404 when no data."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_fetch.return_value = None

        response = self.client.get("/api/fundamentals-db/INVALID")

        self.assertEqual(response.status_code, 404)
        self.assertIn("No fundamental data", response.json()["detail"])
        mock_conn.close.assert_called_once()

    @patch("db_timescale.get_conn")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_fundamentals_db_error(self, mock_fetch, mock_get_conn):
        """Test fundamentals-db endpoint returns 500 on error."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_fetch.side_effect = Exception("DB error")

        response = self.client.get("/api/fundamentals-db/AAPL")

        self.assertEqual(response.status_code, 500)
        mock_conn.close.assert_called_once()

    @patch("db_timescale.get_conn")
    def test_db_stats_endpoint(self, mock_get_conn):
        """Test db stats endpoint returns table statistics."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        from datetime import datetime

        mock_cursor.fetchone.side_effect = [
            {
                "total_rows": 1000000,
                "tickers": 5000,
                "most_recent_date": datetime(2024, 1, 15),
                "oldest_date": datetime(2020, 1, 1),
            },
            {
                "total_rows": 8000,
                "tickers": 4000,
                "last_fetched": datetime(2024, 1, 15),
            },
            {
                "total_rows": 500000,
                "tickers": 4500,
                "most_recent_date": datetime(2024, 1, 15),
            },
            [{"ticker": "XYZ", "last_date": datetime(2023, 6, 1)}],
        ]
        mock_get_conn.return_value = mock_conn

        response = self.client.get("/api/db/stats")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("price_history", data)
        self.assertIn("fundamentals", data)
        self.assertIn("technical_indicators", data)
        self.assertIn("stalest_tickers", data)
        mock_conn.close.assert_called_once()

    @patch("db_timescale.get_conn")
    def test_db_stats_endpoint_error(self, mock_get_conn):
        """Test db stats endpoint returns 500 on error."""
        mock_get_conn.side_effect = Exception("DB connection failed")

        response = self.client.get("/api/db/stats")

        self.assertEqual(response.status_code, 500)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.ensure_ollama")
    @patch("flow.get_money_flow_stocks")
    def test_money_flow_screener(
        self, mock_get_money_flow, mock_ensure_ollama, mock_set_cache, mock_get_cache
    ):
        """Test money flow screener endpoint."""
        mock_get_money_flow.return_value = [
            {"symbol": "AAPL", "money_flow": 1500000000, "change_pct": 2.5},
            {"symbol": "MSFT", "money_flow": 1200000000, "change_pct": 1.8},
        ]

        response = self.client.get(
            "/api/screener/money-flow?period=day&direction=in&limit=25"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        mock_set_cache.assert_called_once()

    @patch("db.get_cached_data")
    @patch("flow.ensure_ollama")
    @patch("flow.get_money_flow_stocks")
    def test_money_flow_screener_cached(
        self, mock_get_money_flow, mock_ensure_ollama, mock_get_cache
    ):
        """Test money flow screener returns cached data."""
        cached_data = [{"symbol": "AAPL", "money_flow": 1500000000}]
        mock_get_cache.return_value = cached_data

        response = self.client.get("/api/screener/money-flow?period=day&direction=in")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), cached_data)
        mock_get_money_flow.assert_not_called()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow.ensure_ollama")
    @patch("flow.get_money_flow_stocks")
    def test_money_flow_screener_error(
        self, mock_get_money_flow, mock_ensure_ollama, mock_set_cache, mock_get_cache
    ):
        """Test money flow screener returns 500 on error."""
        mock_get_money_flow.side_effect = Exception("Ollama error")

        response = self.client.get("/api/screener/money-flow")

        self.assertEqual(response.status_code, 500)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow_api.get_fundamentals_payload")
    def test_batch_fundamentals(
        self, mock_get_fundamentals, mock_set_cache, mock_get_cache
    ):
        """Test batch fundamentals endpoint."""
        mock_get_fundamentals.side_effect = [
            {"symbol": "AAPL", "pe_ratio": 25.5},
            {"symbol": "GOOGL", "pe_ratio": 28.0},
        ]

        response = self.client.post("/api/batch/fundamentals", json=["AAPL", "GOOGL"])

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("AAPL", data)
        self.assertIn("GOOGL", data)
        self.assertEqual(data["AAPL"]["pe_ratio"], 25.5)
        self.assertEqual(data["GOOGL"]["pe_ratio"], 28.0)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow_api.get_fundamentals_payload")
    def test_batch_fundamentals_partial_error(
        self, mock_get_fundamentals, mock_set_cache, mock_get_cache
    ):
        """Test batch fundamentals handles partial errors."""
        mock_get_fundamentals.side_effect = [
            {"symbol": "AAPL", "pe_ratio": 25.5},
            Exception("Failed to fetch"),
        ]

        response = self.client.post("/api/batch/fundamentals", json=["AAPL", "INVALID"])

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("AAPL", data)
        self.assertIn("INVALID", data)
        self.assertIn("error", data["INVALID"])

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow_api.get_price_history_payload")
    def test_batch_price_history(
        self, mock_get_price_history, mock_set_cache, mock_get_cache
    ):
        """Test batch price history endpoint."""
        mock_get_price_history.side_effect = [
            {"data": [{"Date": "2024-01-01", "Close": 150.0}]},
            {"data": [{"Date": "2024-01-01", "Close": 140.0}]},
        ]

        response = self.client.post("/api/batch/price-history", json=["AAPL", "GOOGL"])

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("AAPL", data)
        self.assertIn("GOOGL", data)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow_api.get_price_history_payload")
    def test_batch_price_history_partial_error(
        self, mock_get_price_history, mock_set_cache, mock_get_cache
    ):
        """Test batch price history handles partial errors."""
        mock_get_price_history.side_effect = [
            {"data": [{"Date": "2024-01-01", "Close": 150.0}]},
            Exception("Failed to fetch"),
        ]

        response = self.client.post(
            "/api/batch/price-history", json=["AAPL", "INVALID"]
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("AAPL", data)
        self.assertIn("INVALID", data)
        self.assertIn("error", data["INVALID"])

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.get_conn")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_export_fundamentals_json(
        self, mock_fetch, mock_get_conn, mock_set_cache, mock_get_cache
    ):
        """Test export fundamentals endpoint returns JSON format."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_fetch.return_value = {
            "ticker": "AAPL",
            "short_name": "Apple Inc.",
            "market_cap": 3000000000000,
            "trailing_pe": 25.5,
        }

        response = self.client.get("/api/export/fundamentals/AAPL?format=json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ticker"], "AAPL")
        mock_conn.close.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.get_conn")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_export_fundamentals_csv(
        self, mock_fetch, mock_get_conn, mock_set_cache, mock_get_cache
    ):
        """Test export fundamentals endpoint returns CSV format."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_fetch.return_value = {
            "ticker": "AAPL",
            "short_name": "Apple Inc.",
            "market_cap": 3000000000000,
        }

        response = self.client.get("/api/export/fundamentals/AAPL?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", response.headers["content-disposition"])
        self.assertIn("AAPL_fundamentals.csv", response.headers["content-disposition"])
        mock_conn.close.assert_called_once()

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.get_conn")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_export_fundamentals_invalid_format(
        self, mock_fetch, mock_get_conn, mock_set_cache, mock_get_cache
    ):
        """Test export fundamentals rejects invalid format."""
        response = self.client.get("/api/export/fundamentals/AAPL?format=xml")

        self.assertEqual(response.status_code, 400)
        self.assertIn("csv", response.json()["detail"])

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow_api.get_price_history_payload")
    def test_export_price_history_json(
        self, mock_get_price_history, mock_set_cache, mock_get_cache
    ):
        """Test export price history endpoint returns JSON format."""
        mock_get_price_history.return_value = {
            "data": [
                {"Date": "2024-01-01", "Close": 150.0, "Volume": 1000000},
                {"Date": "2024-01-02", "Close": 152.0, "Volume": 1100000},
            ]
        }

        response = self.client.get("/api/export/price-history/AAPL?format=json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertEqual(len(data["data"]), 2)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow_api.get_price_history_payload")
    def test_export_price_history_csv(
        self, mock_get_price_history, mock_set_cache, mock_get_cache
    ):
        """Test export price history endpoint returns CSV format."""
        mock_get_price_history.return_value = {
            "data": [
                {"Date": "2024-01-01", "Close": 150.0, "Volume": 1000000},
                {"Date": "2024-01-02", "Close": 152.0, "Volume": 1100000},
            ]
        }

        response = self.client.get("/api/export/price-history/AAPL?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", response.headers["content-disposition"])
        self.assertIn("AAPL_price_history.csv", response.headers["content-disposition"])

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("flow_api.get_price_history_payload")
    def test_export_price_history_invalid_format(
        self, mock_get_price_history, mock_set_cache, mock_get_cache
    ):
        """Test export price history rejects invalid format."""
        mock_get_price_history.return_value = {"data": []}

        response = self.client.get("/api/export/price-history/AAPL?format=xml")

        self.assertEqual(response.status_code, 400)
        self.assertIn("csv", response.json()["detail"])

    def test_export_fundamentals_invalid_format(self):
        """Test export fundamentals returns 400 for invalid format."""
        response = self.client.get("/api/export/fundamentals/AAPL?format=xml")
        self.assertEqual(response.status_code, 400)

    def test_export_price_history_invalid_format(self):
        """Test export price history returns 400 for invalid format."""
        response = self.client.get("/api/export/price-history/AAPL?format=xml")
        self.assertEqual(response.status_code, 400)

    @patch("db.get_cached_data", return_value=None)
    @patch("db.set_cached_data")
    @patch("db_timescale.get_conn")
    @patch("db_timescale.fetch_latest_fundamentals")
    def test_fundamentals_db_with_filters(
        self, mock_fetch, mock_get_conn, mock_set_cache, mock_get_cache
    ):
        """Test fundamentals-db endpoint with query filters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [
            {
                "ticker": "AAPL",
                "sector": "Technology",
                "market_cap": 3000000000000,
                "trailing_pe": 25.5,
                "dividend_yield": 0.005,
                "return_on_equity": 0.55,
                "debt_to_equity": 1.5,
            }
        ]
        mock_get_conn.return_value = mock_conn

        response = self.client.get(
            "/api/fundamentals-db?sector=Technology&min_market_cap=1000000000000&max_pe=30&min_dividend_yield=0.001"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(data["count"], 1)
        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
