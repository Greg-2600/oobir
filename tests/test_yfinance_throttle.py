"""Offline tests for yfinance throttling and transport error mapping."""

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import requests
from curl_cffi import requests as curl_requests
from fastapi.testclient import TestClient
from yfinance.exceptions import YFRateLimitError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow
import flow_api


def _http_429_error(exc_type):
    response = SimpleNamespace(status_code=429)
    if exc_type is requests.exceptions.HTTPError:
        response = requests.Response()
        response.status_code = 429
    return exc_type("429 Too Many Requests", response=response)


class TestYFinanceThrottle(unittest.TestCase):
    """Exercise genuine yfinance failures through the FastAPI endpoints."""

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

    def _assert_rate_limited(self, exc):
        with patch("flow.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = exc

            response = self.client.get("/api/price-history/AAPL")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["Retry-After"], "60")
        self.assertIn("rate limiting", response.json()["detail"])

    def test_yfinance_rate_limit_returns_503_with_retry_after(self):
        self._assert_rate_limited(YFRateLimitError())

    def test_requests_http_429_returns_503_with_retry_after(self):
        self._assert_rate_limited(_http_429_error(requests.exceptions.HTTPError))

    def test_curl_cffi_http_429_returns_503_with_retry_after(self):
        self._assert_rate_limited(_http_429_error(curl_requests.exceptions.HTTPError))

    def _assert_transport_failure(self, exc):
        with patch("flow.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = exc

            response = self.client.get("/api/price-history/AAPL")

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Retry-After", response.headers)
        self.assertIn("unreachable", response.json()["detail"])

    def test_requests_connection_error_returns_503(self):
        self._assert_transport_failure(requests.exceptions.ConnectionError("down"))

    def test_requests_timeout_returns_503(self):
        self._assert_transport_failure(requests.exceptions.Timeout("timed out"))

    def test_curl_cffi_connection_error_returns_503(self):
        self._assert_transport_failure(curl_requests.exceptions.ConnectionError("down"))

    def test_curl_cffi_timeout_returns_503(self):
        self._assert_transport_failure(curl_requests.exceptions.Timeout("timed out"))

    @patch("flow.get_fundamentals", return_value=None)
    def test_invalid_ticker_still_returns_200_null(self, _mock_get_fundamentals):
        response = self.client.get("/api/fundamentals/INVALID")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())

    @patch("db.get_cached_data", return_value=[])
    def test_cached_empty_payload_is_unchanged(self, _mock_get_cached_data):
        response = self.client.get("/api/price-history/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_cli_helper_still_returns_none_on_rate_limit(self):
        with patch("flow.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = YFRateLimitError()

            result = flow.get_price_history("AAPL")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
