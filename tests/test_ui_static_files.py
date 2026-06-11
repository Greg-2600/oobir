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
            "crypto.html",
            "metals.html",
            "commodities.html",
        ]:
            self.assertIn(f'href="{href}"', html)


# ---------------------------------------------------------------------------
# Shared nav contract helpers
# ---------------------------------------------------------------------------

ALL_NAV_PAGES = [
    "search.html",
    "index.html",
    "screener.html",
    "markets.html",
    "crypto.html",
    "metals.html",
    "commodities.html",
]


def _assert_shared_header(test_case: unittest.TestCase, html: str) -> None:
    """Assert canonical app-header structure is present."""
    test_case.assertIn('class="app-header"', html)
    test_case.assertIn('class="app-header-content"', html)
    test_case.assertIn('class="app-header-left"', html)
    test_case.assertIn('class="app-brand"', html)
    test_case.assertIn('class="app-nav"', html)
    for href in ALL_NAV_PAGES:
        test_case.assertIn(f'href="{href}"', html)


class TestNavConsistency(unittest.TestCase):
    """Every page must share the same canonical header/nav structure."""

    def _check_page(self, filename: str) -> None:
        html = (WEB_DIR / filename).read_text(encoding="utf-8")
        _assert_shared_header(self, html)
        # The page itself must be marked active in its own nav
        self.assertIn(f'href="{filename}" class="active"', html)

    def test_search_nav(self):
        """search.html nav is consistent."""
        self._check_page("search.html")

    def test_index_nav(self):
        """index.html nav is consistent."""
        self._check_page("index.html")

    def test_screener_nav(self):
        """screener.html nav is consistent."""
        self._check_page("screener.html")

    def test_markets_nav(self):
        """markets.html nav is consistent."""
        self._check_page("markets.html")

    def test_crypto_nav(self):
        """crypto.html nav is consistent."""
        self._check_page("crypto.html")

    def test_metals_nav(self):
        """metals.html nav is consistent."""
        self._check_page("metals.html")

    def test_commodities_nav(self):
        """commodities.html nav is consistent."""
        self._check_page("commodities.html")


class TestCryptoPageContracts(unittest.TestCase):
    """Ensure crypto.html keeps expected structure."""

    def test_crypto_page_has_grid(self):
        """Crypto page should expose the card grid."""
        html = (WEB_DIR / "crypto.html").read_text(encoding="utf-8")
        self.assertIn('id="crypto-grid"', html)

    def test_crypto_page_has_expected_tickers(self):
        """Crypto page should include major assets."""
        html = (WEB_DIR / "crypto.html").read_text(encoding="utf-8")
        for ticker in ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]:
            self.assertIn(f'data-ticker="{ticker}"', html)

    def test_crypto_page_loads_charts_via_api(self):
        """Chart-loading script should call the price-history API."""
        html = (WEB_DIR / "crypto.html").read_text(encoding="utf-8")
        self.assertIn("api/price-history/", html)
        self.assertIn("loadCryptoCharts", html)


class TestMetalsPageContracts(unittest.TestCase):
    """Ensure metals.html keeps expected structure."""

    def test_metals_page_has_grid(self):
        """Metals page should expose the card grid."""
        html = (WEB_DIR / "metals.html").read_text(encoding="utf-8")
        self.assertIn('id="metals-grid"', html)

    def test_metals_page_has_expected_tickers(self):
        """Metals page should include core futures and ETFs."""
        html = (WEB_DIR / "metals.html").read_text(encoding="utf-8")
        for ticker in ["GC=F", "SI=F", "PL=F", "GLD", "GDX"]:
            self.assertIn(f'data-ticker="{ticker}"', html)

    def test_metals_page_loads_charts_via_api(self):
        """Chart-loading script should call the price-history API."""
        html = (WEB_DIR / "metals.html").read_text(encoding="utf-8")
        self.assertIn("api/price-history/", html)
        self.assertIn("loadMetalsCharts", html)


class TestCommoditiesPageContracts(unittest.TestCase):
    """Ensure commodities.html keeps expected structure."""

    def test_commodities_page_has_grid(self):
        """Commodities page should expose the card grid."""
        html = (WEB_DIR / "commodities.html").read_text(encoding="utf-8")
        self.assertIn('id="commodities-grid"', html)

    def test_commodities_page_has_expected_tickers(self):
        """Commodities page should include energy, grains, softs and livestock."""
        html = (WEB_DIR / "commodities.html").read_text(encoding="utf-8")
        for ticker in ["CL=F", "NG=F", "ZC=F", "ZW=F", "KC=F", "LE=F"]:
            self.assertIn(f'data-ticker="{ticker}"', html)

    def test_commodities_page_section_labels_present(self):
        """Commodities page should have section dividers for each category."""
        html = (WEB_DIR / "commodities.html").read_text(encoding="utf-8")
        for label in ["Energy", "Grains", "Softs", "Livestock"]:
            self.assertIn(label, html)

    def test_commodities_page_loads_charts_via_api(self):
        """Chart-loading script should call the price-history API."""
        html = (WEB_DIR / "commodities.html").read_text(encoding="utf-8")
        self.assertIn("api/price-history/", html)
        self.assertIn("loadCommoditiesCharts", html)


if __name__ == "__main__":
    unittest.main()
