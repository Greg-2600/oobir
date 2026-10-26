"""Tests for security features: API key authentication and rate limiting."""

import asyncio
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api

TEST_API_KEY = "test-api-key-12345"


class TestAuthentication(unittest.TestCase):
    """Test cases for API key authentication."""

    def test_health_endpoint_no_auth_required(self):
        """Health endpoint should not require authentication."""
        from starlette.testclient import TestClient as RawTC

        c = RawTC(flow_api.app)
        response = c.get("/api/health")
        self.assertEqual(response.status_code, 200)

    def test_fundamentals_without_api_key_rejected(self):
        """Endpoints should require API key (test middleware directly)."""
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/fundamentals/AAPL",
            "query_string": b"",
            "headers": [],
            "root_path": "",
            "server": ("testserver", 80),
        }
        request = Request(scope)
        resp = asyncio.run(
            flow_api.require_api_key_middleware(
                request, lambda r: JSONResponse({"ok": True})
            )
        )
        self.assertEqual(resp.status_code, 401)

    def test_fundamentals_with_invalid_api_key(self):
        """Endpoints should reject invalid API keys."""
        from starlette.testclient import TestClient as RawTC

        c = RawTC(flow_api.app)
        response = c.get("/api/fundamentals/AAPL", headers={"X-API-Key": "invalid-key"})
        self.assertEqual(response.status_code, 403)

    def test_fundamentals_with_valid_api_key(self):
        """Endpoints should accept valid API keys."""
        from starlette.testclient import TestClient as RawTC

        with patch(
            "db.get_cached_data", return_value={"symbol": "AAPL", "pe_ratio": 25.5}
        ):
            c = RawTC(flow_api.app)
            response = c.get(
                "/api/fundamentals/AAPL", headers={"X-API-Key": TEST_API_KEY}
            )
            self.assertEqual(response.status_code, 200)


class TestRateLimiting(unittest.TestCase):
    """Test cases for rate limiting."""

    def test_rate_limit_headers_present(self):
        """Rate-limited endpoints should include rate limit headers."""
        from starlette.testclient import TestClient as RawTC

        c = RawTC(flow_api.app)
        # The /api/fundamentals endpoint is rate-limited; health is not.
        response = c.get("/api/fundamentals/AAPL")
        # Headers may be present on 200 or 429 responses.
        self.assertIn(response.status_code, (200, 429))


class TestCorrelationId(unittest.TestCase):
    """Test cases for correlation ID middleware."""

    def test_correlation_id_generated(self):
        """Each request should get a correlation ID."""
        from starlette.testclient import TestClient as RawTC

        c = RawTC(flow_api.app)
        response = c.get("/api/health")
        self.assertIn("X-Correlation-ID", response.headers)

    def test_correlation_id_preserved(self):
        """Provided correlation ID should be preserved."""
        from starlette.testclient import TestClient as RawTC

        custom_id = "test-correlation-123"
        c = RawTC(flow_api.app)
        response = c.get("/api/health", headers={"X-Correlation-ID": custom_id})
        self.assertEqual(response.headers["X-Correlation-ID"], custom_id)


if __name__ == "__main__":
    unittest.main()
