"""Tests for batch endpoints and data export functionality."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestBatchEndpoints(unittest.TestCase):
    """Test cases for batch endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)
        self.api_key = "dev-api-key-change-in-production"

    @patch("flow_api.get_fundamentals_payload")
    def test_batch_fundamentals(self, mock_payload):
        """Test batch fundamentals endpoint."""
        mock_payload.side_effect = lambda s: {"symbol": s, "pe_ratio": 25.5}

        response = self.client.post(
            "/api/batch/fundamentals",
            json=["AAPL", "GOOGL"],
            headers={"X-API-Key": self.api_key}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("AAPL", data)
        self.assertIn("GOOGL", data)

    @patch("flow_api.get_price_history_payload")
    def test_batch_price_history(self, mock_payload):
        """Test batch price history endpoint."""
        mock_payload.side_effect = lambda s: {"symbol": s, "data": []}

        response = self.client.post(
            "/api/batch/price-history",
            json=["AAPL", "MSFT"],
            headers={"X-API-Key": self.api_key}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("AAPL", data)
        self.assertIn("MSFT", data)


class TestExportEndpoints(unittest.TestCase):
    """Test cases for data export endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)
        self.api_key = "dev-api-key-change-in-production"

    @patch("flow_api.get_fundamentals_payload")
    def test_export_fundamentals_csv(self, mock_payload):
        """Test CSV export for fundamentals."""
        mock_payload.return_value = {"symbol": "AAPL", "pe_ratio": 25.5}

        response = self.client.get(
            "/api/export/fundamentals/AAPL?format=csv",
            headers={"X-API-Key": self.api_key}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/csv; charset=utf-8")

    @patch("flow_api.get_fundamentals_payload")
    def test_export_fundamentals_json(self, mock_payload):
        """Test JSON export for fundamentals."""
        mock_payload.return_value = {"symbol": "AAPL", "pe_ratio": 25.5}

        response = self.client.get(
            "/api/export/fundamentals/AAPL?format=json",
            headers={"X-API-Key": self.api_key}
        )
        self.assertEqual(response.status_code, 200)

    @patch("flow_api.get_fundamentals_payload")
    def test_export_invalid_format(self, mock_payload):
        """Test export with invalid format."""
        mock_payload.return_value = {"symbol": "AAPL"}

        response = self.client.get(
            "/api/export/fundamentals/AAPL?format=xml",
            headers={"X-API-Key": self.api_key}
        )
        self.assertEqual(response.status_code, 400)


class TestHealthEndpoints(unittest.TestCase):
    """Test cases for health check endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    def test_health_deps_endpoint(self):
        """Test /health/deps endpoint structure."""
        with patch("requests.get") as mock_get, \
             patch("db.get_cache_stats") as mock_cache, \
             patch("db_timescale.get_conn") as mock_conn:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            mock_cache.return_value = {"entries": 10}
            mock_conn_ctx = MagicMock()
            mock_conn.return_value = mock_conn_ctx
            mock_cursor = MagicMock()
            mock_conn_ctx.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_conn_ctx.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_cursor.execute = MagicMock()

            response = self.client.get("/health/deps")
            self.assertIn("dependencies", response.json())


if __name__ == "__main__":
    unittest.main()
