"""In-process HTTP request metrics rendered in Prometheus text format."""

import math
import threading
from collections import defaultdict

PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"
UNMATCHED_ROUTE = "unmatched"

_KNOWN_METHODS = frozenset(
    {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"}
)
_ERROR_CLASSES = frozenset({"4xx", "5xx", "other"})


def status_class(status_code: int) -> str:
    """Map an HTTP status code to a bounded status class label."""
    if 200 <= status_code < 300:
        return "2xx"
    if 300 <= status_code < 400:
        return "3xx"
    if 400 <= status_code < 500:
        return "4xx"
    if 500 <= status_code < 600:
        return "5xx"
    return "other"


def method_label(method: str) -> str:
    """Map an HTTP method to a bounded label."""
    upper = method.upper()
    return upper if upper in _KNOWN_METHODS else "OTHER"


def escape_label(value: str) -> str:
    """Escape a label value for Prometheus text exposition."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class RequestMetrics:
    """Thread-safe request counts, error counts, and latency totals."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: dict[tuple[str, str, str], int] = defaultdict(int)
        self._errors: dict[tuple[str, str, str], int] = defaultdict(int)
        self._duration_count: dict[tuple[str, str], int] = defaultdict(int)
        self._duration_sum: dict[tuple[str, str], float] = defaultdict(float)

    def record(
        self, method: str, route: str, status_code: int, duration_seconds: float
    ) -> None:
        """Record one completed request."""
        if not math.isfinite(duration_seconds) or duration_seconds < 0:
            duration_seconds = 0.0
        klass = status_class(status_code)
        key = (method_label(method), route, klass)
        duration_key = (key[0], key[1])
        with self._lock:
            self._requests[key] += 1
            if klass in _ERROR_CLASSES:
                self._errors[key] += 1
            self._duration_count[duration_key] += 1
            self._duration_sum[duration_key] += duration_seconds

    def _snapshot(
        self,
    ) -> tuple[
        dict[tuple[str, str, str], int],
        dict[tuple[str, str, str], int],
        dict[tuple[str, str], int],
        dict[tuple[str, str], float],
    ]:
        with self._lock:
            return (
                dict(self._requests),
                dict(self._errors),
                dict(self._duration_count),
                dict(self._duration_sum),
            )

    def render(self) -> str:
        """Render a consistent Prometheus text exposition snapshot."""
        requests, errors, counts, sums = self._snapshot()
        lines = [
            "# HELP oobir_http_requests_total Total HTTP requests handled.",
            "# TYPE oobir_http_requests_total counter",
        ]
        for (method, route, klass), value in sorted(requests.items()):
            lines.append(
                f'oobir_http_requests_total{{method="{escape_label(method)}",'
                f'route="{escape_label(route)}",status_class="{klass}"}} {value}'
            )

        lines.extend(
            [
                "# HELP oobir_http_request_errors_total Total HTTP requests with an error status class.",
                "# TYPE oobir_http_request_errors_total counter",
            ]
        )
        for (method, route, klass), value in sorted(errors.items()):
            lines.append(
                f'oobir_http_request_errors_total{{method="{escape_label(method)}",'
                f'route="{escape_label(route)}",status_class="{klass}"}} {value}'
            )

        lines.extend(
            [
                "# HELP oobir_http_request_duration_seconds Request latency in seconds.",
                "# TYPE oobir_http_request_duration_seconds summary",
            ]
        )
        for method, route in sorted(counts):
            labels = f'method="{escape_label(method)}",route="{escape_label(route)}"'
            lines.append(
                f"oobir_http_request_duration_seconds_count{{{labels}}}"
                f" {counts[(method, route)]}"
            )
            lines.append(
                f"oobir_http_request_duration_seconds_sum{{{labels}}}"
                f" {sums[(method, route)]:.6f}"
            )

        return "\n".join(lines) + "\n"


REQUEST_METRICS = RequestMetrics()
