"""Offline tests for dependency health checks used by /health/deps."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
import db_timescale
import flow_api


def _fake_conn():
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = False
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestCacheHealthCheck(unittest.TestCase):
    """Tests for db.check_cache_health with a mocked SQLite connection."""

    def test_ok_runs_trivial_query_and_returns_stats(self):
        conn = _fake_conn()
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = conn
        stats = {"total_entries": 3, "lru_cache_entries": 1, "by_endpoint": []}

        with (
            patch("db.get_db_connection", return_value=conn_cm),
            patch("db.get_cache_stats", return_value=stats),
        ):
            result = db.check_cache_health()

        conn.execute.assert_called_once_with("SELECT 1")
        self.assertEqual(result, {"status": "ok", "stats": stats})

    def test_query_failure_is_degraded_and_sanitized(self):
        conn_cm = MagicMock()
        conn_cm.__enter__.side_effect = RuntimeError("cannot open /secret/cache.db")

        with patch("db.get_db_connection", return_value=conn_cm):
            result = db.check_cache_health()

        self.assertEqual(result["status"], "degraded")
        self.assertNotIn("/secret", str(result))
        self.assertNotIn("cache.db", str(result))

    def test_stats_failure_is_degraded(self):
        conn = _fake_conn()
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = conn

        with (
            patch("db.get_db_connection", return_value=conn_cm),
            patch("db.get_cache_stats", side_effect=RuntimeError("stats down")),
        ):
            result = db.check_cache_health()

        self.assertEqual(result["status"], "degraded")

    def test_stats_error_payload_is_sanitized(self):
        conn = _fake_conn()
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = conn

        with (
            patch("db.get_db_connection", return_value=conn_cm),
            patch("db.get_cache_stats", return_value={"error": "/secret/cache.db"}),
        ):
            result = db.check_cache_health()

        self.assertEqual(result["status"], "degraded")
        self.assertNotIn("/secret", str(result))


class TestTimescaleHealthCheck(unittest.TestCase):
    """Tests for db_timescale.check_health with mocked connections."""

    def test_unconfigured_does_not_attempt_connection(self):
        empty_pg_env = {name: "" for name in db_timescale.PG_ENV_VARS}
        with (
            patch.dict(os.environ, empty_pg_env),
            patch("db_timescale.get_conn") as mock_get_conn,
        ):
            result = db_timescale.check_health()

        self.assertEqual(result, {"status": "unconfigured"})
        mock_get_conn.assert_not_called()

    def test_configured_ok_uses_short_timeout(self):
        conn = _fake_conn()

        with (
            patch("db_timescale.is_configured", return_value=True),
            patch("db_timescale.get_conn", return_value=conn) as mock_get_conn,
        ):
            result = db_timescale.check_health()

        self.assertEqual(result, {"status": "ok"})
        mock_get_conn.assert_called_once_with(
            connect_timeout=db_timescale.HEALTH_CHECK_TIMEOUT_SECONDS
        )
        conn.cursor.return_value.execute.assert_called_once_with("SELECT 1")
        conn.close.assert_called_once()

    def test_configured_failure_is_degraded_and_sanitized(self):
        leaky_error = "host=private-db credential=super-secret"
        with (
            patch("db_timescale.is_configured", return_value=True),
            patch("db_timescale.get_conn", side_effect=RuntimeError(leaky_error)),
        ):
            result = db_timescale.check_health()

        self.assertEqual(result["status"], "degraded")
        self.assertNotIn("private-db", str(result))
        self.assertNotIn("super-secret", str(result))

    def test_get_conn_passes_connect_timeout_when_requested(self):
        with patch("db_timescale.psycopg2.connect") as mock_connect:
            db_timescale.get_conn(connect_timeout=3)

        self.assertEqual(mock_connect.call_args.kwargs["connect_timeout"], 3)


class TestHealthDepsEndpoint(unittest.TestCase):
    """Tests for the /health/deps response shape and status handling."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    def _healthy_ollama(self):
        return patch("requests.get", return_value=MagicMock(status_code=200))

    def _healthy_yfinance(self):
        return patch("yfinance.Ticker")

    def test_reports_ok_cache_and_unconfigured_database(self):
        stats = {"total_entries": 2}
        with (
            self._healthy_ollama(),
            self._healthy_yfinance(),
            patch(
                "db.check_cache_health",
                return_value={"status": "ok", "stats": stats},
            ),
            patch(
                "db_timescale.check_health",
                return_value={"status": "unconfigured"},
            ),
        ):
            response = self.client.get("/health/deps")

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["dependencies"]["cache"]["status"], "ok")
        self.assertEqual(body["dependencies"]["cache"]["stats"], stats)
        self.assertEqual(body["dependencies"]["timescale"]["status"], "unconfigured")
        self.assertIn("ollama", body["dependencies"])
        self.assertIn("yfinance", body["dependencies"])

    def test_degraded_cache_returns_503(self):
        with (
            self._healthy_ollama(),
            self._healthy_yfinance(),
            patch(
                "db.check_cache_health",
                return_value={
                    "status": "degraded",
                    "error": "SQLite cache health check failed",
                },
            ),
            patch(
                "db_timescale.check_health",
                return_value={"status": "unconfigured"},
            ),
        ):
            response = self.client.get("/health/deps")

        body = response.json()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["dependencies"]["cache"]["status"], "degraded")

    def test_degraded_database_returns_503(self):
        with (
            self._healthy_ollama(),
            self._healthy_yfinance(),
            patch(
                "db.check_cache_health",
                return_value={"status": "ok", "stats": {}},
            ),
            patch(
                "db_timescale.check_health",
                return_value={
                    "status": "degraded",
                    "error": "database health check failed",
                },
            ),
        ):
            response = self.client.get("/health/deps")

        body = response.json()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["dependencies"]["timescale"]["status"], "degraded")

    def test_database_error_does_not_leak_connection_details(self):
        leaky_error = "host=private-db credential=super-secret"
        with (
            self._healthy_ollama(),
            self._healthy_yfinance(),
            patch(
                "db.check_cache_health",
                return_value={"status": "ok", "stats": {}},
            ),
            patch("db_timescale.is_configured", return_value=True),
            patch("db_timescale.get_conn", side_effect=RuntimeError(leaky_error)),
        ):
            response = self.client.get("/health/deps")

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private-db", response.text)
        self.assertNotIn("super-secret", response.text)


if __name__ == "__main__":
    unittest.main()
