"""Offline contract tests for the API versioning and deprecation policy."""

import re
import unittest
from datetime import UTC, datetime, timedelta
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = (ROOT / "docs" / "API_VERSIONING.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
FLOW_API = (ROOT / "flow_api.py").read_text(encoding="utf-8")
CITATION = (ROOT / "CITATION.cff").read_text(encoding="utf-8")


def _section(title):
    """Return the body of a level-two section in the policy document."""
    heading = f"## {title}\n"
    start = POLICY.index(heading) + len(heading)
    end = POLICY.find("\n## ", start)
    return POLICY[start:] if end == -1 else POLICY[start:end]


def _table_rows(section):
    """Return data rows from a markdown table, skipping the separator row."""
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows[1:]


class TestApiVersioningPolicy(unittest.TestCase):
    """Keep the published policy aligned with the running app and README."""

    def test_policy_has_all_required_sections(self):
        for heading in (
            "Current version",
            "Compatibility rules",
            "Introducing a new version",
            "Deprecation notices",
            "Deprecation register",
            "Client checklist",
        ):
            with self.subTest(heading=heading):
                self.assertIn(f"## {heading}\n", POLICY)

    def test_documented_version_matches_app_and_citation(self):
        rows = _table_rows(_section("Current version"))
        v1_rows = [row for row in rows if row[0] == "v1"]
        self.assertEqual(len(v1_rows), 1)

        app_version = re.search(r'^\s+version="([^"]+)",', FLOW_API, re.MULTILINE)
        citation_version = re.search(r"^version:\s*(\S+)", CITATION, re.MULTILINE)
        self.assertIsNotNone(app_version)
        self.assertIsNotNone(citation_version)
        self.assertEqual(app_version.group(1), citation_version.group(1))

        row = v1_rows[0]
        self.assertEqual(row[1], app_version.group(1))
        self.assertIn("/api/*", row[2])
        self.assertIn("Current", row[3])

    def test_compatibility_rules_cover_additive_and_breaking_changes(self):
        rules = _section("Compatibility rules")
        for snippet in (
            "new optional request parameters",
            "new response fields",
            "removing or renaming a route",
            "changing a field's type",
            "making an optional parameter required",
            "changing a status code",
            "changing authentication requirements",
            "ignore response fields they do not recognize",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, rules)

    def test_deprecation_notices_define_headers_and_minimum_window(self):
        notices = _section("Deprecation notices")
        for snippet in (
            "`Deprecation: true`",
            "`Sunset`",
            "RFC 8631",
            "RFC 8594",
            "`Link` header",
            "`deprecated` flag",
            "90 days",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, notices)

    def test_deprecation_register_entries_are_well_formed(self):
        register = _section("Deprecation register")
        self.assertIn("_None currently deprecated._", register)
        rows = [
            row
            for row in _table_rows(register)
            if "None currently deprecated" not in row[0]
        ]
        for cells in rows:
            with self.subTest(route=cells[0]):
                self.assertEqual(len(cells), 5)
                announced = datetime.strptime(cells[1], "%Y-%m-%d").replace(tzinfo=UTC)
                sunset = parsedate_to_datetime(cells[2]).astimezone(UTC)
                self.assertEqual(formatdate(sunset, usegmt=True), cells[2])
                self.assertGreaterEqual(sunset - announced, timedelta(days=90))
                self.assertTrue(cells[3])
                self.assertTrue(cells[4])

    def test_readme_links_the_policy(self):
        for snippet in (
            "- [API Versioning and Deprecation Policy](docs/API_VERSIONING.md)",
            "[API versioning and deprecation policy](docs/API_VERSIONING.md)",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, README)


if __name__ == "__main__":
    unittest.main()
