"""Static UI contract tests for frontend HTML/JS assets."""

from pathlib import Path
import re
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"


class TestIndexPageContracts(unittest.TestCase):
    """Ensure index page keeps expected UX structure."""

    def test_results_section_nav_exists_with_expected_targets(self):
        """Results page should include sticky section chips for fast navigation."""
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('class="results-section-nav"', html)
        self.assertIn('id="back-button"', html)
        self.assertIn('id="exploration-rail"', html)
        self.assertIn('id="compare-panel"', html)
        self.assertIn('id="since-last-view"', html)
        self.assertIn('id="revisit-marker-toggle"', html)
        self.assertIn('id="revisit-marker-toggle-status"', html)

        expected_targets = [
            "section-overview",
            "decision-summary",
            "section-price-history",
            "section-fundamentals",
            "section-analyst-targets",
            "section-news",
            "section-options",
        ]

        for target in expected_targets:
            self.assertIn(f'data-target="{target}"', html)

    def test_index_ids_are_unique(self):
        """Duplicate id values can break section-nav and document lookups."""
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        ids = re.findall(r'id="([^"]+)"', html)

        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        self.assertEqual(duplicates, [], f"Duplicate id values found: {duplicates}")

    def test_landing_page_market_radar_exists(self):
        """Landing page should expose the market radar panel."""
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('class="market-radar-section"', html)
        self.assertIn('id="market-radar-grid"', html)


class TestAppJsContracts(unittest.TestCase):
    """Ensure app.js includes UX behavior we rely on."""

    def test_results_section_nav_logic_present(self):
        """Section chips should be wired with smooth-scroll and active-state updates."""
        js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn("function initializeResultsSectionNav()", js)
        self.assertIn("IntersectionObserver", js)
        self.assertIn(".section-chip[data-target]", js)

    def test_exploration_rail_logic_present(self):
        """Results flow should surface back/recent exploration shortcuts."""
        js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn("const RECENT_TICKERS_KEY = 'oobir_recent_tickers'", js)
        self.assertIn("function readStoredArray(key)", js)
        self.assertIn("function writeStoredArray(key, values)", js)
        self.assertIn("const LAST_VIEW_SNAPSHOTS_KEY = 'oobir_last_view_snapshots'", js)
        self.assertIn(
            "const SHOW_REVISIT_MARKERS_KEY = 'oobir_show_revisit_markers'", js
        )
        self.assertIn("function readStoredObject(key)", js)
        self.assertIn("function writeStoredObject(key, value)", js)
        self.assertIn(
            "function renderSinceLastViewBadge(ticker, currentPrice, viewToken)", js
        )
        self.assertIn("Compared against your previous viewed price", js)
        self.assertIn("function renderSeenMarker(ticker)", js)
        self.assertIn("function initializeRevisitMarkerToggle()", js)
        self.assertIn("function setRevisitMarkersEnabled(enabled)", js)
        self.assertIn("function pushRecentTicker(ticker)", js)
        self.assertIn("function getRecentTickers(limit = 5)", js)
        self.assertIn("function renderComparePanel(activeTicker)", js)
        self.assertIn("function addTickerToCompare(ticker)", js)
        self.assertIn("function getCompareSets()", js)
        self.assertIn("function saveCurrentCompareSet(name, tickers)", js)
        self.assertIn("function applyCompareSet(name, activeTicker)", js)
        self.assertIn("function renderCompareSetsMarkup()", js)
        self.assertIn("function renderMarketRadar(stocks)", js)
        self.assertIn("function radarReason(groupKey, item, rank)", js)
        self.assertIn("function buildSparklineSvg(series)", js)
        self.assertIn("function populateSparklineNodes(root)", js)
        self.assertIn("market-radar-item-why", js)
        self.assertIn("compare-sets-list", js)
        self.assertIn("function renderExplorationRail(ticker)", js)
        self.assertIn("exploration-rail", js)
        self.assertIn("recentTickers", js)

    def test_keyboard_shortcuts_present(self):
        """Keyboard shortcuts should support fast search focus."""
        js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn("event.key === '/'", js)
        self.assertIn("event.key.toLowerCase() === 'k'", js)
        self.assertIn("event.ctrlKey || event.metaKey", js)


class TestSearchPageContracts(unittest.TestCase):
    """Ensure search page keeps recent ticker and quick-nav behavior."""

    def test_search_page_recent_ticker_support_present(self):
        """Search page should persist and render recent ticker chips."""
        html = (WEB_DIR / "search.html").read_text(encoding="utf-8")

        self.assertIn("oobir_recent_tickers", html)
        self.assertIn('id="recent-wrap"', html)
        self.assertIn("function renderRecentTickers()", html)

    def test_search_page_top_nav_links_present(self):
        """Search page should provide top-level navigation links."""
        html = (WEB_DIR / "search.html").read_text(encoding="utf-8")

        self.assertIn('class="app-header"', html)
        self.assertIn('class="app-nav"', html)
        for href in [
            "search.html",
            "index.html",
            "screener.html",
            "markets.html",
            "stocks.html",
        ]:
            self.assertIn(f'href="{href}"', html)


if __name__ == "__main__":
    unittest.main()
