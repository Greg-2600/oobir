"""
UI tests for the OOBIR stock analysis platform using Selenium.
Tests cover: page loading, stock search, data display, and API interactions.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class TestHomePageLoad:
    """Test cases for initial page load and UI elements."""

    def test_page_loads(self, browser, base_url):
        """Verify the home page loads successfully."""
        browser.get(base_url)
        assert "OOBIR" in browser.title

    def test_landing_page_visible(self, browser, base_url):
        """Verify landing page and key elements are visible."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        # Check for main logo
        logo = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "unified-logo"))
        )
        assert "OOBIR" in logo.text

        # Check for search form
        search_form = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-form"))
        )
        assert search_form.is_displayed()

        # Check for search input
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        assert search_input.is_displayed()

    def test_search_button_visible(self, browser, base_url):
        """Verify search button is present and clickable."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        search_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        assert search_button.is_displayed()

    def test_home_section_heading_present(self, browser, base_url):
        """Verify a key landing-page heading is displayed."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        heading = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".stocks-grid-section h2"))
        )
        assert "Stock Screener" in heading.text


class TestStockSearch:
    """Test cases for stock search functionality."""

    def test_search_with_valid_ticker(self, browser, base_url, wait_timeout):
        """Search for a valid stock ticker and verify data loads."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        # Find and fill search input
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys("AAPL")

        # Submit search
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        # Wait for results page to load
        wait.until(EC.presence_of_element_located((By.ID, "results-page")))
        assert browser.find_element(By.ID, "results-page").is_displayed()

    def test_search_input_accepts_text(self, browser, base_url):
        """Verify search input accepts text input."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.send_keys("MSFT")

        assert search_input.get_attribute("value") == "MSFT"

    def test_search_input_case_insensitive(self, browser, base_url):
        """Verify search accepts lowercase input."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.send_keys("msft")

        assert search_input.get_attribute("value").upper() == "MSFT"

    def test_empty_search_not_allowed(self, browser, base_url):
        """Verify empty search is prevented."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()

        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        unified_page = browser.find_element(By.ID, "unified-page")
        results_page = browser.find_element(By.ID, "results-page")
        assert "hidden" not in unified_page.get_attribute("class")
        assert "hidden" in results_page.get_attribute("class")


class TestResultsPageDisplay:
    """Test cases for results page and data display."""

    def _search_aapl(self, browser, wait):
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-page").get_attribute("class")
        )
        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

    def test_results_page_shows_company_info(self, browser, base_url, wait_timeout):
        """Verify results page displays company information."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        company_info = wait.until(
            EC.visibility_of_element_located((By.ID, "company-summary-box"))
        )
        assert company_info.is_displayed()

    def test_results_page_shows_stock_header(self, browser, base_url, wait_timeout):
        """Verify stock header is displayed on results."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        header = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "stock-header"))
        )
        assert header.is_displayed()
        assert (
            browser.find_element(By.ID, "stock-symbol").text.strip().upper() == "AAPL"
        )

    def test_back_button_returns_to_home(self, browser, base_url, wait_timeout):
        """Verify clicking results logo navigates back to search page."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        logo = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "logo-small")))
        logo.click()

        wait.until(lambda d: "search.html" in d.current_url)
        assert "search.html" in browser.current_url

    def test_results_sections_visible(self, browser, base_url, wait_timeout):
        """Verify key results sections are present."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        for element_id in [
            "fundamentals-data",
            "analyst-targets-data",
            "technical-signals-data",
            "calendar-data",
        ]:
            element = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
            assert element.is_displayed()


class TestRecommendationsSection:
    """Test cases for strategy and trend recommendation display."""

    def _search_aapl(self, browser, wait):
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

    def test_trading_strategy_card_loads(self, browser, base_url, wait_timeout):
        """Verify trading strategy card appears on results."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        strategy = wait.until(
            EC.visibility_of_element_located((By.ID, "trading-strategy"))
        )
        assert strategy.is_displayed()

    def test_trend_prediction_card_loads(self, browser, base_url, wait_timeout):
        """Verify trend prediction card appears on results."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        trend = wait.until(
            EC.visibility_of_element_located((By.ID, "trend-prediction"))
        )
        assert trend.is_displayed()


class TestDataTables:
    """Test cases for data sections on results page."""

    def _search_aapl(self, browser, wait):
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

    def test_fundamentals_section_loads(self, browser, base_url, wait_timeout):
        """Verify fundamentals section loads and is visible."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        fundamentals = wait.until(
            EC.visibility_of_element_located((By.ID, "fundamentals-data"))
        )
        assert fundamentals.is_displayed()
        assert len(fundamentals.get_attribute("innerHTML")) > 0

    def test_price_history_chart_displays(self, browser, base_url, wait_timeout):
        """Verify price history section displays content."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        price_history = wait.until(
            EC.visibility_of_element_located((By.ID, "price-history-data"))
        )
        assert price_history.is_displayed()
        assert len(price_history.get_attribute("innerHTML")) > 0


class TestUIInteractions:
    """Test cases for UI interactions and responsiveness."""

    def _search(self, browser, wait, ticker):
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys(ticker)
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

    def test_logo_click_returns_home(self, browser, base_url, wait_timeout):
        """Verify clicking results logo navigates to search page."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search(browser, wait, "AAPL")

        logo = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "logo-small")))
        logo.click()
        wait.until(lambda d: "search.html" in d.current_url)
        assert "search.html" in browser.current_url

    def test_enter_key_submits_search(self, browser, base_url, wait_timeout):
        """Verify pressing Enter in search input submits form."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.send_keys("AAPL")
        search_input.send_keys(Keys.RETURN)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )
        assert (
            browser.find_element(By.ID, "stock-symbol").text.strip().upper() == "AAPL"
        )

    def test_compact_search_controls_present(self, browser, base_url, wait_timeout):
        """Verify compact search controls are visible and editable on results."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search(browser, wait, "AAPL")

        compact_form = wait.until(
            EC.visibility_of_element_located((By.ID, "search-form-compact"))
        )
        compact_input = wait.until(
            EC.visibility_of_element_located((By.ID, "ticker-input-compact"))
        )
        compact_submit = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#search-form-compact button[type='submit']")
            )
        )

        compact_input.clear()
        compact_input.send_keys("MSFT")

        assert compact_form.is_displayed()
        assert compact_submit.is_displayed()
        assert compact_input.get_attribute("value") == "MSFT"


class TestErrorHandling:
    """Test cases for error handling and edge cases."""

    def test_invalid_ticker_handling(self, browser, base_url, wait_timeout):
        """Verify invalid ticker is rejected with an error message."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys("INVALID123XYZ")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        error_msg = wait.until(
            EC.visibility_of_element_located((By.ID, "error-message"))
        )
        assert "valid stock ticker" in error_msg.text


class TestEnhancedNavigationUX:
    """Behavior tests for newer navigation and keyboard UX features."""

    @staticmethod
    def _search_aapl(browser, wait):
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

    @staticmethod
    def _search_page_url(base_url):
        return base_url.rstrip("/") + "/search.html"

    def test_section_chip_click_sets_active_and_scrolls(
        self, browser, base_url, wait_timeout
    ):
        """Clicking a section chip should activate it and scroll toward target section."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        price_chip = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".section-chip[data-target='section-price-history']")
            )
        )
        price_chip.click()

        wait.until(
            lambda d: "active"
            in d.find_element(
                By.CSS_SELECTOR, ".section-chip[data-target='section-price-history']"
            ).get_attribute("class")
        )

        top = browser.execute_script(
            "return document.getElementById('section-price-history').getBoundingClientRect().top;"
        )
        assert top < 260

    def test_slash_shortcut_focuses_search_input_on_search_page(
        self, browser, base_url, wait_timeout
    ):
        """Pressing / should focus the primary search input on search page."""
        browser.get(self._search_page_url(base_url))
        wait = WebDriverWait(browser, wait_timeout)

        body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        body.send_keys("/")

        wait.until(lambda d: d.switch_to.active_element.get_attribute("id") == "q")
        assert browser.switch_to.active_element.get_attribute("id") == "q"

    def test_recent_ticker_chip_appears_after_search(
        self, browser, base_url, wait_timeout
    ):
        """Searching from search page should persist ticker and render a recent chip."""
        browser.get(self._search_page_url(base_url))
        wait = WebDriverWait(browser, wait_timeout)

        input_el = wait.until(EC.presence_of_element_located((By.ID, "q")))
        input_el.clear()
        input_el.send_keys("TSLA")
        search_btn = browser.find_element(By.ID, "search-btn")
        search_btn.click()

        wait.until(lambda d: "index.html?ticker=TSLA" in d.current_url)

        browser.get(self._search_page_url(base_url))
        chip = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".recent-chip[data-ticker='TSLA']")
            )
        )
        assert chip.is_displayed()

    def test_special_characters_in_search(self, browser, base_url, wait_timeout):
        """Verify special characters are handled as invalid input."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys("AAPL$#@!")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        error_msg = wait.until(
            EC.visibility_of_element_located((By.ID, "error-message"))
        )
        assert "valid stock ticker" in error_msg.text

    def test_since_last_view_badge_updates_after_revisit(
        self, browser, base_url, wait_timeout
    ):
        """Revisiting a ticker should show a since-last-view delta badge."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        browser.execute_script(
            "window.localStorage.removeItem('oobir_last_view_snapshots');"
            "window.sessionStorage.removeItem('oobir_last_view_snapshots');"
        )

        self._search_aapl(browser, wait)

        first_badge = wait.until(
            EC.visibility_of_element_located((By.ID, "since-last-view"))
        )
        assert "First tracked view" in first_badge.text

        compact_input = wait.until(
            EC.visibility_of_element_located((By.ID, "ticker-input-compact"))
        )
        compact_input.clear()
        compact_input.send_keys("MSFT")
        compact_submit = browser.find_element(
            By.CSS_SELECTOR, "#search-form-compact button[type='submit']"
        )
        compact_submit.click()
        wait.until(
            lambda d: d.find_element(By.ID, "stock-symbol").text.strip().upper()
            == "MSFT"
        )

        compact_input = wait.until(
            EC.visibility_of_element_located((By.ID, "ticker-input-compact"))
        )
        compact_input.clear()
        compact_input.send_keys("AAPL")
        compact_submit = browser.find_element(
            By.CSS_SELECTOR, "#search-form-compact button[type='submit']"
        )
        compact_submit.click()
        wait.until(
            lambda d: d.find_element(By.ID, "stock-symbol").text.strip().upper()
            == "AAPL"
        )

        wait.until(
            lambda d: "since last view"
            in d.find_element(By.ID, "since-last-view").text.lower()
        )
        revisit_badge_text = browser.find_element(By.ID, "since-last-view").text
        assert "since last view" in revisit_badge_text.lower()

    def test_since_last_view_badge_has_explanatory_tooltip(
        self, browser, base_url, wait_timeout
    ):
        """Revisit badge should expose comparison details in title tooltip text."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        browser.execute_script(
            "window.localStorage.removeItem('oobir_last_view_snapshots');"
            "window.sessionStorage.removeItem('oobir_last_view_snapshots');"
        )

        self._search_aapl(browser, wait)

        compact_input = wait.until(
            EC.visibility_of_element_located((By.ID, "ticker-input-compact"))
        )
        compact_input.clear()
        compact_input.send_keys("MSFT")
        browser.find_element(
            By.CSS_SELECTOR, "#search-form-compact button[type='submit']"
        ).click()
        wait.until(
            lambda d: d.find_element(By.ID, "stock-symbol").text.strip().upper()
            == "MSFT"
        )

        compact_input = wait.until(
            EC.visibility_of_element_located((By.ID, "ticker-input-compact"))
        )
        compact_input.clear()
        compact_input.send_keys("AAPL")
        browser.find_element(
            By.CSS_SELECTOR, "#search-form-compact button[type='submit']"
        ).click()
        wait.until(
            lambda d: d.find_element(By.ID, "stock-symbol").text.strip().upper()
            == "AAPL"
        )

        badge = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#since-last-view .since-last-view-badge")
            )
        )
        wait.until(
            lambda d: "Compared against your previous viewed price"
            in (badge.get_attribute("title") or "")
        )
        assert "Compared against your previous viewed price" in (
            badge.get_attribute("title") or ""
        )

    def test_revisit_marker_toggle_hides_and_shows_related_markers(
        self, browser, base_url, wait_timeout
    ):
        """Header toggle should hide/show revisit markers in related stock cards."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search_aapl(browser, wait)

        first_related = wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#related-stocks-data .related-stock-item[data-ticker]",
                )
            )
        )
        related_ticker = first_related.get_attribute("data-ticker")
        assert related_ticker

        browser.execute_script(
            "const key='oobir_last_view_snapshots';"
            "const now=Date.now()-3600000;"
            "const ticker=arguments[0];"
            "const payload={}; payload[ticker]={price:100, updatedAt:now};"
            "window.localStorage.setItem(key, JSON.stringify(payload));"
            "window.sessionStorage.setItem(key, JSON.stringify(payload));",
            related_ticker,
        )

        toggle = wait.until(
            EC.element_to_be_clickable((By.ID, "revisit-marker-toggle"))
        )
        if not toggle.is_selected():
            toggle.click()

        toggle.click()
        wait.until(
            lambda d: d.find_element(By.ID, "revisit-marker-toggle-status").text.strip()
            == "Off"
        )
        related_item = wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    f"#related-stocks-data .related-stock-item[data-ticker='{related_ticker}']",
                )
            )
        )
        assert len(related_item.find_elements(By.CSS_SELECTOR, ".seen-marker")) == 0

        toggle = wait.until(
            EC.element_to_be_clickable((By.ID, "revisit-marker-toggle"))
        )
        toggle.click()
        wait.until(
            lambda d: d.find_element(By.ID, "revisit-marker-toggle-status").text.strip()
            == "On"
        )
        related_item = wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    f"#related-stocks-data .related-stock-item[data-ticker='{related_ticker}']",
                )
            )
        )
        wait.until(
            lambda d: len(related_item.find_elements(By.CSS_SELECTOR, ".seen-marker"))
            >= 1
        )
        assert len(related_item.find_elements(By.CSS_SELECTOR, ".seen-marker")) >= 1


class TestUnifiedTopHeader:
    """Cross-page checks for the unified top header/nav experience."""

    @staticmethod
    def _page_url(base_url, path):
        base = base_url.rstrip("/")
        if path.startswith("/"):
            return base + path
        return base + "/" + path

    def test_header_and_nav_present_on_primary_pages(
        self, browser, base_url, wait_timeout
    ):
        """Every main page should expose the same app-header and app-nav."""
        wait = WebDriverWait(browser, wait_timeout)
        pages = [
            "search.html",
            "index.html",
            "screener.html",
            "markets.html",
            "stocks.html",
        ]

        for path in pages:
            browser.get(self._page_url(base_url, path))
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app-header")))
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app-nav")))

            links = browser.find_elements(By.CSS_SELECTOR, ".app-nav a")
            hrefs = [link.get_attribute("href") or "" for link in links]
            assert any("search.html" in href for href in hrefs)
            assert any("index.html" in href for href in hrefs)
            assert any("screener.html" in href for href in hrefs)
            assert any("markets.html" in href for href in hrefs)
            assert any("stocks.html" in href for href in hrefs)

    def test_navigation_link_from_search_to_markets(
        self, browser, base_url, wait_timeout
    ):
        """Top nav should let users move across pages without dead ends."""
        wait = WebDriverWait(browser, wait_timeout)
        browser.get(self._page_url(base_url, "search.html"))

        markets_link = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".app-nav a[href='markets.html']")
            )
        )
        markets_link.click()

        wait.until(lambda d: "markets.html" in d.current_url)
        assert "markets.html" in browser.current_url


class TestRelatedStocksExplorer:
    """Tests for related-stock discovery links on results page."""

    @staticmethod
    def _search(browser, wait, ticker):
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "ticker-input"))
        )
        search_input.clear()
        search_input.send_keys(ticker)
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

    def test_related_stocks_card_visible_after_search(
        self, browser, base_url, wait_timeout
    ):
        """Results page should show related-stock exploration card."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search(browser, wait, "TSLA")

        card = wait.until(
            EC.visibility_of_element_located((By.ID, "related-stocks-data"))
        )
        assert card.is_displayed()

    def test_related_stock_link_navigates_to_new_ticker(
        self, browser, base_url, wait_timeout
    ):
        """Clicking a related stock should navigate to another ticker detail page."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)
        self._search(browser, wait, "TSLA")

        links = wait.until(
            EC.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "#related-stocks-data .related-stock-item[data-ticker]",
                )
            )
        )
        assert len(links) >= 1

        first = links[0]
        ticker = first.get_attribute("data-ticker")
        assert ticker

        first.click()
        wait.until(lambda d: f"ticker={ticker}" in d.current_url)

        symbol = wait.until(EC.visibility_of_element_located((By.ID, "stock-symbol")))
        assert symbol.text.strip().upper() == ticker.upper()
