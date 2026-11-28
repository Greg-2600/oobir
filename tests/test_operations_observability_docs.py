"""Offline contract tests for the observability guidance in OPERATIONS.md."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from request_metrics import REQUEST_METRICS

ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = (ROOT / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


class TestObservabilityGuidance(unittest.TestCase):
    """Keep the documented dashboards and alerts aligned with /metrics."""

    def test_guidance_covers_scraping_dashboards_and_alerts(self):
        self.assertIn("## Dashboards and alerts", OPERATIONS)
        for snippet in (
            "scrape_configs:",
            "metrics_path: /metrics",
            'targets: ["app:2010"]',
            'X-API-Key: "<api-key-from-secret-store>"',
            "sum by (status_class) (rate(oobir_http_requests_total[5m]))",
            "OobirHigh5xxRate",
            "OobirSlowRequests",
            "curl -fsS http://app:2010/health/deps",
            "X-Correlation-ID",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, OPERATIONS)

    def test_documented_metric_families_match_exposition(self):
        exposed = set(re.findall(r"(?m)^# TYPE (\S+)", REQUEST_METRICS.render()))
        self.assertTrue(exposed)

        documented = set()
        for token in re.findall(r"\b(oobir_http_[a-z0-9_]+)", OPERATIONS):
            family = token
            for suffix in ("_count", "_sum", "_bucket", "_created"):
                if family.endswith(suffix):
                    family = family[: -len(suffix)]
                    break
            with self.subTest(token=token):
                self.assertIn(family, exposed)
            documented.add(family)

        self.assertEqual(exposed, documented)

    def test_readme_points_to_the_operational_guidance(self):
        self.assertIn(
            "See [OPERATIONS.md](docs/OPERATIONS.md) for scrape configuration, "
            "dashboard panels, and starter alerts.",
            README,
        )
        self.assertIn("metrics dashboards and alerts", README)


if __name__ == "__main__":
    unittest.main()
