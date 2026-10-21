"""
Selenium tests for verifying the UI loads correctly at http://IP:PORT/?ticker=CHTR
and related URL parameter functionality.

Tests cover:
- Landing page (index.html) loads without ticker
- URL parameter ?ticker=CHTR auto-loads stock data
- API base URL resolution (2010 vs 8000 mismatch fix)
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestLandingPageLoads:
    """Verify the landing page (index.html) loads at the root URL."""

    def test_landing_page_loads_without_ticker(self, browser, base_url):
        """index.html should load successfully when accessed without ?ticker param."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        wait.until(EC.title_contains("OOBIR"))
        assert "OOBIR" in browser.title

    def test_landing_page_shows_search_input(self, browser, base_url):
        """Landing page should display a search input."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        search_input = wait.until(
            EC.visibility_of_element_located((By.ID, "ticker-input"))
        )
        assert search_input.is_displayed()

    def test_landing_page_shows_logo(self, browser, base_url):
        """Landing page should display the OOBIR logo."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        logo = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "unified-logo"))
        )
        assert logo.is_displayed()
        assert "OOBIR" in logo.text

    def test_landing_page_shows_stocks_grid(self, browser, base_url):
        """Landing page should display the stocks grid section."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        grid_section = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "stocks-grid-section"))
        )
        assert grid_section.is_displayed()


class TestTickerURLEDParameter:
    """Test that ?ticker=CHTR URL parameter auto-loads stock data."""

    def test_ticker_in_url_auto_searches(self, browser, base_url):
        """http://host/?ticker=CHTR should auto-search for CHTR stock."""
        browser.get(f"{base_url}/?ticker=CHTR")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class"),
            message="Results container should be visible after auto-search"
        )

        symbol = wait.until(
            EC.text_to_be_present_in_element((By.ID, "stock-symbol"), "CHTR")
        )
        stock_symbol = browser.find_element(By.ID, "stock-symbol")
        assert stock_symbol.text.strip().upper() == "CHTR"

    def test_ticker_url_shows_results_page(self, browser, base_url):
        """Results page should be visible when accessing via ?ticker=CHTR."""
        browser.get(f"{base_url}/?ticker=CHTR")
        wait = WebDriverWait(browser, 30)

        results_page = wait.until(
            EC.visibility_of_element_located((By.ID, "results-page"))
        )
        assert results_page.is_displayed()

    def test_ticker_url_loads_fundamentals(self, browser, base_url):
        """Fundamentals data should load when accessing via ?ticker=CHTR."""
        browser.get(f"{base_url}/?ticker=CHTR")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

        fundamentals = wait.until(
            EC.visibility_of_element_located((By.ID, "fundamentals-data"))
        )
        assert fundamentals.is_displayed()
        assert len(fundamentals.get_attribute("innerHTML").strip()) > 0

    def test_ticker_url_loads_price_history(self, browser, base_url):
        """Price history section should load when accessing via ?ticker=CHTR."""
        browser.get(f"{base_url}/?ticker=CHTR")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

        price_history = wait.until(
            EC.visibility_of_element_located((By.ID, "price-history-data"))
        )
        assert price_history.is_displayed()

    def test_ticker_url_lowercase_works(self, browser, base_url):
        """http://host/?ticker=chtr (lowercase) should work and uppercase to CHTR."""
        browser.get(f"{base_url}/?ticker=chtr")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

        stock_symbol = wait.until(
            EC.visibility_of_element_located((By.ID, "stock-symbol"))
        )
        assert stock_symbol.text.strip().upper() == "CHTR"


class TestAPIConnection:
    """Verify the UI correctly connects to the API."""

    def test_api_base_url_is_configured(self, browser, base_url):
        """API_BASE_URL should be configured (not undefined/null)."""
        browser.get(f"{base_url}/?ticker=AAPL")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

        api_base = browser.execute_script("return window.OOBIR_API_BASE || window.CONFIG?.API_BASE_URL || window.API_BASE_URL;")
        assert api_base is not None and len(api_base) > 0, f"API_BASE_URL should be configured, got: {api_base}"

    def test_fundamentals_section_exists(self, browser, base_url):
        """Fundamentals section should exist and render on results page."""
        browser.get(f"{base_url}/?ticker=AAPL")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

        fundamentals = wait.until(
            EC.visibility_of_element_located((By.ID, "fundamentals-data"))
        )
        assert fundamentals is not None


class TestSearchFromResultsPage:
    """Test that searching for a new ticker from results page works."""

    def test_search_from_ticker_url_page(self, browser, base_url):
        """After loading via ?ticker=CHTR, search for AAPL should work."""
        browser.get(f"{base_url}/?ticker=CHTR")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

        compact_input = wait.until(
            EC.visibility_of_element_located((By.ID, "ticker-input-compact"))
        )
        compact_input.clear()
        compact_input.send_keys("AAPL")

        submit = browser.find_element(
            By.CSS_SELECTOR, "#search-form-compact button[type='submit']"
        )
        submit.click()

        wait.until(
            lambda d: d.find_element(By.ID, "stock-symbol").text.strip().upper() == "AAPL",
            message="Stock symbol should update to AAPL after search"
        )

        stock_symbol = browser.find_element(By.ID, "stock-symbol")
        assert stock_symbol.text.strip().upper() == "AAPL"

    def test_back_to_home_from_ticker_url(self, browser, base_url):
        """Clicking logo should return to home (search page) from ?ticker= URL."""
        browser.get(f"{base_url}/?ticker=CHTR")
        wait = WebDriverWait(browser, 30)

        wait.until(
            lambda d: "hidden"
            not in d.find_element(By.ID, "results-container").get_attribute("class")
        )

        logo = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "logo-small"))
        )
        logo.click()

        wait.until(lambda d: "index.html" in d.current_url or "search.html" in d.current_url)
        assert "index.html" in browser.current_url or "search.html" in browser.current_url
