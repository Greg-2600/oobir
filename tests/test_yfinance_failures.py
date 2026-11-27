"""Offline tests for clear API errors when yfinance is throttling or down."""

import os
import sys
import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


def _history_frame(rows: int = 2) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="D")
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(rows)],
            "High": [101.0 + i for i in range(rows)],
            "Low": [99.0 + i for i in range(rows)],
            "Close": [100.5 + i for i in range(rows)],
            "Volume": [1_000 + i for i in range(rows)],
        },
        index=dates,
    )


class TestYFinanceFailures(unittest.TestCase):
    """Exercise yfinance failure paths through the FastAPI endpoints."""

    def setUp(self):
        self.client = TestClient(flow_api.app)
        self.db_patches = (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("db_timescale.get_conn", side_effect=RuntimeError("db offline")),
        )
        for db_patch in self.db_patches:
            db_patch.start()
            self.addCleanup(db_patch.stop)

    @patch("flow.yf.Ticker")
    def test_rate_limited_price_history_returns_503_with_retry_after(self, mock_ticker):
        mock_ticker.return_value.history.side_effect = Exception(
            "429 Too Many Requests: rate limited"
        )

        response = self.client.get("/api/price-history/AAPL")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["Retry-After"], "60")
        self.assertIn("throttling", response.json()["detail"])

    @patch("flow.yf.Ticker")
    def test_network_error_fundamentals_returns_503(self, mock_ticker):
        mock_ticker.side_effect = ConnectionError("network down")

        response = self.client.get("/api/fundamentals/AAPL")

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Retry-After", response.headers)
        self.assertIn("unreachable", response.json()["detail"])

    @patch("flow.yf.Ticker")
    def test_empty_price_history_returns_503(self, mock_ticker):
        mock_ticker.return_value.history.return_value = pd.DataFrame()

        response = self.client.get("/api/price-history/AAPL")

        self.assertEqual(response.status_code, 503)
        self.assertIn("No price history returned", response.json()["detail"])

    @patch("flow.yf.Ticker")
    def test_empty_fundamentals_returns_503(self, mock_ticker):
        mock_ticker.return_value.info = {}

        response = self.client.get("/api/fundamentals/AAPL")

        self.assertEqual(response.status_code, 503)
        self.assertIn("No fundamentals returned", response.json()["detail"])

    @patch("flow.yf.Ticker")
    def test_successful_fundamentals_are_unchanged(self, mock_ticker):
        mock_ticker.return_value.info = {"symbol": "AAPL", "currentPrice": 190.0}

        response = self.client.get("/api/fundamentals/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["symbol"], "AAPL")
        self.assertEqual(response.json()["currentPrice"], 190.0)

    @patch("flow.yf.Ticker")
    def test_successful_price_history_is_unchanged(self, mock_ticker):
        mock_ticker.return_value.history.return_value = _history_frame()

        response = self.client.get("/api/price-history/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 2)


if __name__ == "__main__":
    unittest.main()
