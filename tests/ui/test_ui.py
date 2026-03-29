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
