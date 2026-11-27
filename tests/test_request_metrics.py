"""Offline tests for in-process request metrics and the /metrics endpoint."""

import itertools
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api
from request_metrics import (
    PROMETHEUS_CONTENT_TYPE,
    UNMATCHED_ROUTE,
    RequestMetrics,
    escape_label,
    method_label,
    status_class,
)

TEST_API_KEY = "test-api-key-12345"


def _steady_clock():
    """Return 0.5-second durations regardless of how often the clock is read."""
    ticks = itertools.count()

    def perf_counter():
        return (next(ticks) // 2) * 0.5

    return perf_counter


class TestMetricHelpers(unittest.TestCase):
    """Tests for bounded label helpers."""

    def test_status_class(self):
        for code, expected in [
            (200, "2xx"),
            (299, "2xx"),
            (301, "3xx"),
            (404, "4xx"),
            (503, "5xx"),
            (99, "other"),
            (600, "other"),
        ]:
            self.assertEqual(status_class(code), expected)

    def test_method_label_is_bounded(self):
        self.assertEqual(method_label("GET"), "GET")
        self.assertEqual(method_label("post"), "POST")
        self.assertEqual(method_label("CUSTOM-VERB"), "OTHER")

    def test_escape_label(self):
        self.assertEqual(escape_label('a\\b"c\nd'), 'a\\\\b\\"c\\nd')


class TestRequestMetrics(unittest.TestCase):
    """Tests for the thread-safe metrics accumulator and text rendering."""

    def test_empty_render_has_metric_families_but_no_samples(self):
        body = RequestMetrics().render()
        for line in (
            "# HELP oobir_http_requests_total Total HTTP requests handled.",
            "# TYPE oobir_http_requests_total counter",
            "# TYPE oobir_http_request_errors_total counter",
            "# TYPE oobir_http_request_duration_seconds summary",
        ):
            self.assertIn(line, body)
        self.assertNotIn("oobir_http_requests_total{", body)

    def test_counts_and_errors_by_status_class(self):
        metrics = RequestMetrics()
        metrics.record("GET", "/api/fundamentals/{symbol}", 200, 0.25)
        metrics.record("GET", "/api/fundamentals/{symbol}", 503, 0.75)
        metrics.record("GET", "/api/fundamentals/{symbol}", 302, 0.01)
        body = metrics.render()

        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/api/fundamentals/{symbol}",'
            'status_class="2xx"} 1',
            body,
        )
        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/api/fundamentals/{symbol}",'
            'status_class="5xx"} 1',
            body,
        )
        self.assertIn(
            'oobir_http_request_errors_total{method="GET",'
            'route="/api/fundamentals/{symbol}",status_class="5xx"} 1',
            body,
        )
        self.assertNotIn(
            'oobir_http_request_errors_total{method="GET",'
            'route="/api/fundamentals/{symbol}",status_class="2xx"}',
            body,
        )

    def test_latency_summary_count_and_sum(self):
        metrics = RequestMetrics()
        metrics.record("GET", "/health", 200, 0.25)
        metrics.record("GET", "/health", 200, 0.75)
        body = metrics.render()
        self.assertIn(
            'oobir_http_request_duration_seconds_count{method="GET",route="/health"} 2',
            body,
        )
        self.assertIn(
            'oobir_http_request_duration_seconds_sum{method="GET",route="/health"} 1.000000',
            body,
        )

    def test_invalid_duration_is_clamped_to_zero(self):
        metrics = RequestMetrics()
        metrics.record("GET", "/health", 200, float("nan"))
        metrics.record("GET", "/health", 200, float("inf"))
        metrics.record("GET", "/health", 200, -1.0)
        body = metrics.render()
        self.assertIn(
            'oobir_http_request_duration_seconds_count{method="GET",route="/health"} 3',
            body,
        )
        self.assertIn(
            'oobir_http_request_duration_seconds_sum{method="GET",route="/health"} 0.000000',
            body,
        )

    def test_concurrent_records_are_not_lost(self):
        metrics = RequestMetrics()

        def record_many():
            for _ in range(100):
                metrics.record("GET", "/health", 200, 0.01)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: record_many(), range(8)))

        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/health",status_class="2xx"} 800',
            metrics.render(),
        )


class TestMetricsEndpoint(unittest.TestCase):
    """Tests for /metrics authentication and request recording."""

    def setUp(self):
        self.metrics = RequestMetrics()
        patcher = patch.object(flow_api, "REQUEST_METRICS", self.metrics)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(flow_api.app)

    def test_metrics_requires_api_key(self):
        missing = self.client.get("/metrics", headers={"X-API-Key": ""})
        invalid = self.client.get("/metrics", headers={"X-API-Key": "wrong-key"})
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(invalid.status_code, 403)

        body = self.client.get("/metrics").text
        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/metrics",status_class="4xx"} 2',
            body,
        )
        self.assertIn(
            'oobir_http_request_errors_total{method="GET",route="/metrics",status_class="4xx"} 2',
            body,
        )

    def test_metrics_returns_prometheus_text(self):
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], PROMETHEUS_CONTENT_TYPE)
        self.assertIn("# TYPE oobir_http_requests_total counter", response.text)
        self.assertIn(
            "# TYPE oobir_http_request_duration_seconds summary", response.text
        )

    def test_requests_are_recorded_under_route_templates(self):
        payload = {"symbol": "AAPL", "pe_ratio": 25.5}
        with (
            patch("flow_api.time.perf_counter", side_effect=_steady_clock()),
            patch("db.get_cached_data", return_value=payload),
        ):
            self.client.get("/api/fundamentals/AAPL")
            self.client.get(
                "/api/fundamentals/MSFT", headers={"X-API-Key": "wrong-key"}
            )
            self.client.get("/health")
            self.client.get("/no-such-route")
            body = self.client.get("/metrics").text

        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/api/fundamentals/{symbol}",'
            'status_class="2xx"} 1',
            body,
        )
        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/api/fundamentals/{symbol}",'
            'status_class="4xx"} 1',
            body,
        )
        self.assertIn(
            f'oobir_http_requests_total{{method="GET",route="{UNMATCHED_ROUTE}",'
            'status_class="4xx"} 1',
            body,
        )
        self.assertNotIn("/api/fundamentals/AAPL", body)
        self.assertIn(
            'oobir_http_request_duration_seconds_count{method="GET",'
            'route="/api/fundamentals/{symbol}"} 2',
            body,
        )
        self.assertIn(
            'oobir_http_request_duration_seconds_sum{method="GET",'
            'route="/api/fundamentals/{symbol}"} 1.000000',
            body,
        )

    def test_degraded_dependency_is_counted_as_5xx(self):
        with (
            patch("requests.get", return_value=MagicMock(status_code=200)),
            patch("yfinance.Ticker"),
            patch("db.check_cache_health", return_value={"status": "degraded"}),
            patch("db_timescale.check_health", return_value={"status": "unconfigured"}),
        ):
            response = self.client.get("/health/deps")
            body = self.client.get("/metrics").text

        self.assertEqual(response.status_code, 503)
        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/health/deps",'
            'status_class="5xx"} 1',
            body,
        )
        self.assertIn(
            'oobir_http_request_errors_total{method="GET",route="/health/deps",'
            'status_class="5xx"} 1',
            body,
        )

    def test_unhandled_exception_is_counted_as_500(self):
        failing = TestClient(flow_api.app, raise_server_exceptions=False)
        with patch("flow_api.db.get_cache_stats", side_effect=RuntimeError("boom")):
            response = failing.get("/api/cache-info")
            body = self.client.get("/metrics").text

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            'oobir_http_requests_total{method="GET",route="/api/cache-info",'
            'status_class="5xx"} 1',
            body,
        )


if __name__ == "__main__":
    unittest.main()
