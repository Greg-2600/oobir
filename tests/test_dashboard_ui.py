"""Static contract tests for the Market Briefing dashboard page.

These tests guard the dashboard's HTML structure, its inline JavaScript and
its dependency on the REST API. They are intentionally static (no browser
or network required) so they run fast in CI.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"
DASHBOARD = WEB_DIR / "dashboard.html"
FLOW_API = REPO_ROOT / "flow_api.py"

# Every section the dashboard renders. Each one must exist as an element id.
DASHBOARD_SECTION_IDS = [
    "index-snapshot",
    "futures-row",
    "fear-greed-wrap",
    "movers-body",
    "ml-signals",
    "earn-list",
    "macro-list",
    "sector-hm",
]

# IDs that must be unique on the page (no duplicates allowed).
DASHBOARD_REQUIRED_IDS = DASHBOARD_SECTION_IDS + [
    "update-time",
    "theme-toggle",
]


def _strip_js_noise(script: str) -> str:
    """Remove comments and string literals so regex scans don't false-positive.

    This is a single-pass scanner rather than a chain of regexes: sequential
    regex passes get confused by an apostrophe inside a double-quoted string
    (e.g. ``"don't"``), which can swallow braces and make a perfectly valid
    script look unbalanced.
    """
    out = []
    index = 0
    length = len(script)

    while index < length:
        char = script[index]
        following = script[index + 1] if index + 1 < length else ""

        # Line comment
        if char == "/" and following == "/":
            newline = script.find("\n", index)
            index = length if newline == -1 else newline
            continue

        # Block comment
        if char == "/" and following == "*":
            end = script.find("*/", index + 2)
            index = length if end == -1 else end + 2
            continue

        # String literal (single, double or template)
        if char in ('"', "'", "`"):
            quote = char
            index += 1
            while index < length:
                if script[index] == "\\":
                    index += 2
                    continue
                if script[index] == quote:
                    index += 1
                    break
                index += 1
            out.append('""')
            continue

        out.append(char)
        index += 1

    return "".join(out)


def _scoped_declarations(script: str):
    """Yield (scope_path, kind, name) for declarations found in ``script``.

    ``scope_path`` identifies the enclosing block chain, so two declarations
    only collide when they sit in the *same* scope. Two different functions
    may each declare their own ``const rows`` without conflict — but two
    ``const score`` inside one function is a fatal SyntaxError that stops
    the browser parsing the whole script.
    """
    cleaned = _strip_js_noise(script)
    decl_re = re.compile(r"(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)")

    scope = [0]
    next_scope_id = 1
    found = []
    i = 0
    length = len(cleaned)

    while i < length:
        char = cleaned[i]
        if char == "{":
            scope.append(next_scope_id)
            next_scope_id += 1
        elif char == "}":
            if len(scope) > 1:
                scope.pop()
        elif char.isalpha() or char in "_$":
            # Only start a word at a token boundary.
            if i == 0 or not (cleaned[i - 1].isalnum() or cleaned[i - 1] in "_$"):
                match = decl_re.match(cleaned, i)
                if match:
                    found.append(
                        (tuple(scope), match.group(0).split()[0], match.group(1))
                    )
                    i = match.end()
                    continue
        i += 1

    return found


def _inline_scripts(html: str) -> list:
    """Return the contents of every inline <script> block (no src=)."""
    return re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S)


class TestDashboardPageContracts(unittest.TestCase):
    """Ensure dashboard.html keeps its expected structure."""

    def test_dashboard_file_exists(self):
        """The dashboard page should exist on disk."""
        self.assertTrue(DASHBOARD.exists(), "web/dashboard.html is missing")

    def test_dashboard_has_all_section_containers(self):
        """Every dashboard section should have a stable element id."""
        html = DASHBOARD.read_text(encoding="utf-8")
        for section_id in DASHBOARD_SECTION_IDS:
            self.assertIn(f'id="{section_id}"', html, f"missing section #{section_id}")

    def test_dashboard_ids_are_unique(self):
        """Duplicate ids break getElementById lookups and CSS targeting."""
        html = DASHBOARD.read_text(encoding="utf-8")
        ids = re.findall(r'id="([^"]+)"', html)

        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        self.assertEqual(duplicates, [], f"Duplicate id values found: {duplicates}")

    def test_dashboard_has_no_missing_required_ids(self):
        """Core dashboard ids must all be present exactly once."""
        html = DASHBOARD.read_text(encoding="utf-8")
        for required in DASHBOARD_REQUIRED_IDS:
            self.assertIn(f'id="{required}"', html, f"missing id #{required}")

    def test_dashboard_has_no_horizontal_overflow_guard(self):
        """The page should pin to the viewport instead of scrolling the body."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("overflow: hidden", html)
        self.assertIn("height: 100vh", html)

    def test_dashboard_uses_relative_api_base(self):
        """API calls must use the serving origin so CORS never breaks."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("const API = window.location.origin", html)
        self.assertNotIn("192.168.1.248", html)

    def test_dashboard_links_to_core_pages(self):
        """The nav should expose the main analysis pages."""
        html = DASHBOARD.read_text(encoding="utf-8")
        for href in [
            "search.html",
            "index.html",
            "screener.html",
            "markets.html",
            "predictions.html",
            "portfolio.html",
            "watchlist.html",
            "calendar.html",
        ]:
            self.assertIn(f'href="{href}"', html)

    def test_dashboard_marks_itself_active_in_nav(self):
        """The dashboard should be the active nav item on its own page."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn('href="dashboard.html" class="active"', html)


class TestDashboardLoadingStates(unittest.TestCase):
    """Ensure each section surfaces a loading indicator while data is in flight."""

    def test_dashboard_defines_loading_styles(self):
        """Loading indicator styles should exist."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn(".loading-wrap", html)
        self.assertIn(".loading-dots", html)

    def test_dashboard_sections_start_in_loading_state(self):
        """Sections should be marked as loading before the first fetch."""
        html = DASHBOARD.read_text(encoding="utf-8")
        for section_id in DASHBOARD_SECTION_IDS:
            pattern = rf'id="{section_id}"[^>]*data-loading="true"'
            self.assertRegex(
                html, pattern, f"#{section_id} should start with data-loading=true"
            )

    def test_dashboard_has_set_loading_helper(self):
        """A helper should drive the per-section loading indicator."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("function setLoading(el)", html)

    def test_dashboard_refresh_sets_loading_before_fetching(self):
        """refreshAll should show loading state before awaiting the API."""
        html = DASHBOARD.read_text(encoding="utf-8")
        script = "\n".join(_inline_scripts(html))
        refresh_body = script.split("async function refreshAll()", 1)[-1]
        refresh_body = refresh_body.split("\n    }", 1)[0]

        self.assertIn("setLoading(", refresh_body)
        self.assertIn("await Promise.all(", refresh_body)
        # Loading must be applied before the awaits resolve.
        self.assertLess(
            refresh_body.index("setLoading("),
            refresh_body.index("await Promise.all("),
            "loading state must be set before awaiting the API",
        )


class TestDashboardCompanyNames(unittest.TestCase):
    """Ensure tickers are displayed with readable company names."""

    def test_dashboard_loads_names_from_fundamentals_db(self):
        """Names should come from the bulk fundamentals endpoint."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("/api/fundamentals-db", html)
        self.assertIn("function loadCompanyNames()", html)

    def test_dashboard_has_fallback_for_missing_names(self):
        """Tickers absent from the bulk list should fall back to per-symbol lookup."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("function loadMissingNames(", html)
        self.assertIn("/api/fundamentals/${t}", html)

    def test_dashboard_has_static_index_etf_names(self):
        """Index ETFs are not equities and need hardcoded fund names."""
        html = DASHBOARD.read_text(encoding="utf-8")
        for ticker in ["SPY", "QQQ", "DIA", "IWM"]:
            self.assertRegex(html, rf"{ticker}:\s*'")

    def test_dashboard_renders_company_names_in_sections(self):
        """Movers, ML signals and earnings should all show company names."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn('class="company tip-host"', html)
        self.assertIn('class="sig-name tip-host"', html)
        self.assertIn('class="name tip-host"', html)

    def test_dashboard_movers_table_has_company_column(self):
        """The movers table should include a company name column."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("<th>Company</th>", html)


class TestDashboardTooltips(unittest.TestCase):
    """Ensure the floating tooltip system is wired up."""

    def test_dashboard_defines_tooltip_element_and_styles(self):
        """Tooltip container and styles should be present."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("#oobir-tip", html)
        self.assertIn("function initTooltip()", html)

    def test_dashboard_tooltip_reads_data_attributes(self):
        """Tooltips should be driven by data-tip attributes."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("data-tip", html)
        self.assertIn("data-tip-title", html)
        self.assertIn("data-tip-sub", html)

    def test_dashboard_tooltip_clamps_to_viewport(self):
        """The tooltip should flip near viewport edges rather than overflow."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("function positionTip(", html)
        script = "\n".join(_inline_scripts(html))
        position_body = script.split("function positionTip(", 1)[-1].split(
            "\n    }", 1
        )[0]
        # Horizontally it must stay inside the viewport...
        self.assertIn("window.innerWidth", position_body)
        # ...and vertically it must flip below the cursor when there is no room above.
        self.assertIn("e.clientY - rect.height", position_body)
        self.assertIn("e.clientY + pad", position_body)


class TestDashboardRefreshBehaviour(unittest.TestCase):
    """Ensure the page refreshes itself hourly and renders in the right order."""

    def test_dashboard_auto_refreshes_hourly(self):
        """The briefing should refresh on a 60-minute interval."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("setInterval(refreshAll, 60 * 60 * 1000)", html)

    def test_dashboard_renders_instant_sections_before_awaiting(self):
        """Futures and earnings need no API and must not wait on the network."""
        script = "\n".join(_inline_scripts(DASHBOARD.read_text(encoding="utf-8")))
        refresh_body = script.split("async function refreshAll()", 1)[-1]
        refresh_body = refresh_body.split("\n    }", 1)[0]

        load_futures = refresh_body.index("loadFutures();")
        load_earnings = refresh_body.index("loadEarnings();")
        await_all = refresh_body.index("await Promise.all(")

        self.assertLess(load_futures, await_all)
        self.assertLess(load_earnings, await_all)

    def test_dashboard_exposes_manual_refresh(self):
        """A manual refresh button should be wired to refreshAll."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn('onclick="refreshAll()"', html)

    def test_dashboard_has_theme_toggle(self):
        """The dashboard should respect the shared theme preference."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("oobir_theme", html)
        self.assertIn('id="theme-toggle"', html)


class TestDashboardScriptValidity(unittest.TestCase):
    """Guard against JavaScript syntax mistakes that freeze the whole page.

    A single undeclared duplicate (``const score`` twice, for example) makes
    the browser reject the entire inline script block, which leaves the page
    stuck on its loading state forever with no console-visible cause. These
    checks catch that class of mistake without needing a JS engine.
    """

    def test_dashboard_has_inline_script(self):
        """The page must ship its logic inline."""
        scripts = _inline_scripts(DASHBOARD.read_text(encoding="utf-8"))
        self.assertTrue(scripts, "dashboard.html has no inline <script> block")

    def test_no_duplicate_declarations_in_same_scope(self):
        """No two declarations may share a name within the same scope.

        A duplicate ``const`` in one scope is a SyntaxError that makes the
        browser discard the entire script block — the page then sits on its
        loading state forever with no visible error.
        """
        script = "\n".join(_inline_scripts(DASHBOARD.read_text(encoding="utf-8")))

        seen = {}
        duplicates = []
        for scope, kind, name in _scoped_declarations(script):
            key = (scope, name)
            if key in seen:
                duplicates.append(f"{name} (declared twice in the same scope)")
            else:
                seen[key] = kind

        self.assertEqual(
            duplicates, [], f"Duplicate declarations in the same scope: {duplicates}"
        )

    def test_no_duplicate_function_declarations(self):
        """Function names must be unique across the script."""
        script = "\n".join(_inline_scripts(DASHBOARD.read_text(encoding="utf-8")))

        seen = {}
        duplicates = []
        for scope, kind, name in _scoped_declarations(script):
            if kind != "function":
                continue
            key = (scope, name)
            if key in seen:
                duplicates.append(f"{name} (declared twice in the same scope)")
            else:
                seen[key] = kind

        self.assertEqual(
            duplicates, [], f"Duplicate function declarations: {duplicates}"
        )

    def test_braces_are_balanced(self):
        """Braces, brackets and parentheses must balance in the inline script."""
        script = "\n".join(_inline_scripts(DASHBOARD.read_text(encoding="utf-8")))
        cleaned = _strip_js_noise(script)

        for opener, closer, label in [
            ("{", "}", "braces"),
            ("[", "]", "brackets"),
            ("(", ")", "parentheses"),
        ]:
            self.assertEqual(
                cleaned.count(opener),
                cleaned.count(closer),
                f"Unbalanced {label} in dashboard script",
            )

    def test_no_undefined_helper_calls(self):
        """Every locally-defined helper used for loading should exist."""
        script = "\n".join(_inline_scripts(DASHBOARD.read_text(encoding="utf-8")))
        cleaned = _strip_js_noise(script)

        for helper in ["setLoading", "api", "companyName", "fullName", "tipAttrs"]:
            self.assertRegex(
                cleaned,
                rf"function\s+{helper}\s*\(",
                f"helper {helper}() is used but never defined",
            )


class TestDashboardApiContract(unittest.TestCase):
    """Ensure every endpoint the dashboard calls actually exists."""

    def test_dashboard_endpoints_exist_in_api(self):
        """Dashboard API calls must map to real routes."""
        html = DASHBOARD.read_text(encoding="utf-8")
        api_source = FLOW_API.read_text(encoding="utf-8")

        routes = set()
        for match in re.finditer(r'@app\.get\("(/api/[^"]+)"', api_source):
            route = match.group(1)
            # Collapse FastAPI path params so /api/predict/{symbol} matches
            # a call to /api/predict/AAPL.
            route = re.sub(r"\{[^}]+\}", "*", route)
            routes.add(route)

        called = set()
        for match in re.finditer(r"api\(\s*[`'](/api/[^`'?]+)", html):
            called.add(match.group(1))

        self.assertTrue(called, "dashboard makes no API calls")

        for path in sorted(called):
            # /api/price-history/${t} -> /api/price-history/*
            normalized = re.sub(r"\$\{[^}]+\}", "*", path)
            # Match either an exact route or a parameterised route prefix.
            match_found = any(
                route == normalized
                or (route.endswith("*") and normalized.startswith(route[:-1]))
                for route in routes
            )
            self.assertTrue(
                match_found,
                f"dashboard calls {path} but no matching route exists in flow_api.py",
            )

    def test_dashboard_uses_x_api_key_header(self):
        """Requests must carry the API key header."""
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("X-API-Key", html)


class TestDashboardDiscovery(unittest.TestCase):
    """Ensure the dashboard is reachable from the header nav and main pages.

    A dashboard nobody can find is worthless, so every page's primary nav
    must link to it, and the two main entry points should feature it
    prominently rather than only in a long nav strip.
    """

    def _nav_pages(self):
        """Every HTML page that renders the shared app-nav."""
        return sorted(p.name for p in WEB_DIR.glob("*.html"))

    def test_every_page_nav_links_to_dashboard(self):
        """Each page's primary nav should offer a link to the dashboard."""
        missing = []
        for name in self._nav_pages():
            html = (WEB_DIR / name).read_text(encoding="utf-8")
            nav = re.search(r'<nav class="app-nav".*?</nav>', html, flags=re.S)
            if not nav:
                continue
            if 'href="dashboard.html"' not in nav.group(0):
                missing.append(name)

        self.assertEqual(missing, [], f"Pages without a dashboard nav link: {missing}")

    def test_dashboard_nav_link_is_last_in_nav(self):
        """The dashboard link should sit at the end of the nav for consistency."""
        out_of_place = []
        for name in self._nav_pages():
            html = (WEB_DIR / name).read_text(encoding="utf-8")
            nav = re.search(r'<nav class="app-nav".*?</nav>', html, flags=re.S)
            if not nav:
                continue
            links = re.findall(r'<a href="([^"]+)"', nav.group(0))
            if "dashboard.html" in links and links[-1] != "dashboard.html":
                out_of_place.append(f"{name}: {links[-1]}")

        self.assertEqual(
            out_of_place, [], f"Dashboard link is not last: {out_of_place}"
        )

    def test_dashboard_is_active_on_its_own_page(self):
        """The dashboard should be marked active in its own nav."""
        html = (WEB_DIR / "dashboard.html").read_text(encoding="utf-8")
        self.assertIn('href="dashboard.html" class="active"', html)

    def test_no_other_page_marks_dashboard_active(self):
        """Only the dashboard itself may mark the link active."""
        offenders = []
        for name in self._nav_pages():
            if name == "dashboard.html":
                continue
            html = (WEB_DIR / name).read_text(encoding="utf-8")
            if 'href="dashboard.html" class="active"' in html:
                offenders.append(name)

        self.assertEqual(
            offenders, [], f"Pages wrongly marking dashboard active: {offenders}"
        )

    def test_main_page_has_briefing_promo(self):
        """index.html should feature the dashboard in a prominent banner."""
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="briefing-promo"', html)
        self.assertIn('href="dashboard.html"', html)
        self.assertIn("Market Briefing", html)

    def test_briefing_promo_is_an_anchor_to_dashboard(self):
        """The promo must be a real link, not a div with a click handler."""
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        promo = re.search(r'<a class="briefing-promo"[^>]*>', html)
        self.assertIsNotNone(promo, "briefing promo should be an <a> element")
        self.assertIn('href="dashboard.html"', promo.group(0))

    def test_search_page_has_market_briefing_quick_link(self):
        """The landing page's quick links should include the briefing."""
        html = (WEB_DIR / "search.html").read_text(encoding="utf-8")
        row = re.search(r'<div class="link-row".*?</div>', html, flags=re.S)
        self.assertIsNotNone(row, "search page should have a quick-link row")
        self.assertIn('href="dashboard.html"', row.group(0))
        self.assertIn("Market Briefing", row.group(0))

    def test_briefing_promo_styles_defined(self):
        """The promo banner needs its own styles in the shared stylesheet."""
        css = (WEB_DIR / "styles.css").read_text(encoding="utf-8")
        for selector in [
            ".briefing-promo",
            ".briefing-promo-icon",
            ".briefing-promo-body",
            ".briefing-promo-title",
            ".briefing-promo-badge",
            ".briefing-promo-sub",
            ".briefing-promo-cta",
        ]:
            self.assertIn(selector, css, f"missing style {selector}")

    def test_briefing_promo_has_dark_theme_variant(self):
        """The promo must be legible in dark mode too."""
        css = (WEB_DIR / "styles.css").read_text(encoding="utf-8")
        self.assertIn('[data-theme="dark"] .briefing-promo', css)
        self.assertIn('[data-theme="dark"] .briefing-promo-title', css)
        self.assertIn('[data-theme="dark"] .briefing-promo-sub', css)


class TestPageScriptValidity(unittest.TestCase):
    """Guard every page's inline JavaScript against syntax errors.

    A single malformed token — ``row.Reported EPS`` instead of
    ``row['Reported EPS']`` — is a SyntaxError that makes the browser discard
    the whole inline script block. The page then renders but never works,
    with no visible clue in the UI.

    These checks are static and dependency-free: they look for the specific
    mistake patterns rather than running a full JS parser.
    """

    def _inline_script_blocks(self, path):
        return _inline_scripts((WEB_DIR / path).read_text(encoding="utf-8"))

    def test_no_bare_property_names_with_spaces(self):
        """Multi-word API keys must use bracket notation, not dot notation."""
        # `new Set(...)` and friends are keyword sequences, not property access.
        keywords = {
            "new",
            "return",
            "typeof",
            "instanceof",
            "in",
            "of",
            "await",
            "delete",
            "void",
            "case",
            "do",
            "else",
            "yield",
            "throw",
        }
        offenders = []
        for path in sorted(p.name for p in WEB_DIR.glob("*.html")):
            for block in self._inline_script_blocks(path):
                cleaned = _strip_js_noise(block)
                # `obj.Word Word` — a dot followed by two identifiers.
                for match in re.finditer(
                    r"\.\s*([A-Za-z_$][\w$]*)\s+([A-Za-z_$][\w$]*)", cleaned
                ):
                    first, second = match.group(1), match.group(2)
                    if first in keywords:
                        continue
                    offenders.append(f"{path}: .{first} {second}")

        self.assertEqual(offenders, [], f"Invalid dotted property access: {offenders}")

    def test_no_known_mangled_tickers(self):
        """Sector/ETF tickers must be plain ASCII symbols."""
        offenders = []
        for path in sorted(p.name for p in WEB_DIR.glob("*.html")):
            html = (WEB_DIR / path).read_text(encoding="utf-8")
            for match in re.finditer(r"ticker:\s*'([^']*)'", html):
                ticker = match.group(1)
                if not ticker:
                    continue
                if not ticker.isascii() or not ticker.isalnum():
                    offenders.append(f"{path}: ticker '{ticker}'")

        self.assertEqual(offenders, [], f"Mangled ticker values: {offenders}")

    def test_every_page_with_inline_script_has_balanced_braces(self):
        """Inline scripts must have balanced braces, brackets and parens."""
        problems = []
        for path in sorted(p.name for p in WEB_DIR.glob("*.html")):
            for index, block in enumerate(self._inline_script_blocks(path)):
                cleaned = _strip_js_noise(block)
                for opener, closer, label in [
                    ("{", "}", "braces"),
                    ("[", "]", "brackets"),
                    ("(", ")", "parentheses"),
                ]:
                    if cleaned.count(opener) != cleaned.count(closer):
                        problems.append(f"{path} block {index}: unbalanced {label}")

        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
