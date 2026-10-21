"""Tests for security features: API key authentication and rate limiting."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestAuthentication(unittest.TestCase):
    """Test cases for API key authentication."""

    def setUp(self):
        """Set up test client with API key."""
        self.client = TestClient(flow_api.app)
        self.api_key = "dev-api-key-change-in-production"

    def test_health_endpoint_no_auth_required(self):
        """Health endpoint should not require authentication."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

    def test_fundamentals_without_api_key(self):
        """Endpoints should require API key."""
        response = self.client.get("/api/fundamentals/AAPL")
        self.assertEqual(response.status_code, 401)

    def test_fundamentals_with_invalid_api_key(self):
        """Endpoints should reject invalid API keys."""
        response = self.client.get(
            "/api/fundamentals/AAPL",
            headers={"X-API-Key": "invalid-key"}
        )
        self.assertEqual(response.status_code, 403)

    def test_fundamentals_with_valid_api_key(self):
        """Endpoints should accept valid API keys."""
        with patch("db.get_cached_data", return_value={"symbol": "AAPL", "pe_ratio": 25.5}):
            response = self.client.get(
                "/api/fundamentals/AAPL",
                headers={"X-API-Key": self.api_key}
            )
            self.assertEqual(response.status_code, 200)


class TestRateLimiting(unittest.TestCase):
    """Test cases for rate limiting."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    def test_rate_limit_headers_present(self):
        """Responses should include rate limit headers."""
        response = self.client.get("/api/health")
        self.assertIn("X-RateLimit", response.headers.keys())


class TestCorrelationId(unittest.TestCase):
    """Test cases for correlation ID middleware."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    def test_correlation_id_generated(self):
        """Each request should get a correlation ID."""
        response = self.client.get("/api/health")
        self.assertIn("X-Correlation-ID", response.headers)

    def test_correlation_id_preserved(self):
        """Provided correlation ID should be preserved."""
        custom_id = "test-correlation-123"
        response = self.client.get(
            "/api/health",
            headers={"X-Correlation-ID": custom_id}
        )
        self.assertEqual(response.headers["X-Correlation-ID"], custom_id)


if __name__ == "__main__":
    unittest.main()
