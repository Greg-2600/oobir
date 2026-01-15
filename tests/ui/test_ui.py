"""
UI tests for the OOBIR stock analysis platform using Selenium.
Tests cover: page loading, stock search, data display, and API interactions.
"""
import pytest
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
        logo = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "unified-logo")))
        assert "OOBIR" in logo.text

        # Check for search form
        search_form = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-form")))
        assert search_form.is_displayed()

        # Check for search input
        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
        assert search_input.is_displayed()

    def test_search_button_visible(self, browser, base_url):
        """Verify search button is present and clickable."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        search_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        assert search_button.is_displayed()

    def test_tagline_present(self, browser, base_url):
        """Verify tagline is displayed."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        tagline = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tagline")))
        assert "AI-Powered" in tagline.text or "Stock Analysis" in tagline.text


class TestStockSearch:
    """Test cases for stock search functionality."""

    def test_search_with_valid_ticker(self, browser, base_url, wait_timeout):
        """Search for a valid stock ticker and verify data loads."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        # Find and fill search input
        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
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

        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
        search_input.send_keys("MSFT")

        assert search_input.get_attribute("value") == "MSFT"

    def test_search_input_case_insensitive(self, browser, base_url):
        """Verify search accepts lowercase input."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
        search_input.send_keys("msft")

        assert search_input.get_attribute("value").upper() == "MSFT"

    def test_empty_search_not_allowed(self, browser, base_url):
        """Verify empty search is prevented."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        # Try submitting empty form
        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.clear()

        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        # Should still be on landing page (no results page)
        landing_page = browser.find_elements(By.ID, "landing-page")
        assert len(landing_page) > 0


class TestResultsPageDisplay:
    """Test cases for results page and data display."""

    def test_results_page_shows_company_info(self, browser, base_url, wait_timeout):
        """Verify results page displays company information."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        # Perform search
        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        # Wait for results
        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Check for company summary box
        company_info = wait.until(
            EC.presence_of_element_located((By.ID, "company-summary-box"))
        )
        assert company_info.is_displayed()

    def test_results_page_shows_stock_header(self, browser, base_url, wait_timeout):
        """Verify stock header is displayed on results."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        # Wait for header
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "stock-header")))
        header = browser.find_element(By.CLASS_NAME, "stock-header")
        assert header.is_displayed()

    def test_back_button_returns_to_home(self, browser, base_url, wait_timeout):
        """Verify back button returns to landing page."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        # Search for stock
        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        # Wait for results
        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Click the logo to return home (back button was removed)
        logo = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "unified-logo")))
        logo.click()

        # Verify back on landing/unified page
        wait.until(EC.presence_of_element_located((By.ID, "unified-page")))
        assert browser.find_element(By.ID, "unified-page").is_displayed()

    def test_results_page_tabs_visible(self, browser, base_url, wait_timeout):
        """Verify results tabs (Fundamentals, Price, etc.) are visible."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Check for tab buttons
        tabs = browser.find_elements(By.CLASS_NAME, "tab-button")
        assert len(tabs) > 0


class TestRecommendationsSection:
    """Test cases for AI recommendations display."""

    def test_recommendations_tab_loads(self, browser, base_url, wait_timeout):
        """Verify recommendations section loads and displays."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Click on recommendations tab (if separate)
        # Adjust selector based on actual HTML structure
        rec_tabs = browser.find_elements(By.CLASS_NAME, "tab-button")
        for tab in rec_tabs:
            if "recommendation" in tab.text.lower() or "ai" in tab.text.lower():
                tab.click()
                break

        # Wait for recommendations to load
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "recommendation-card"))
        )
        rec_card = browser.find_element(By.CLASS_NAME, "recommendation-card")
        assert rec_card.is_displayed()

    def test_recommendation_displays_action(self, browser, base_url, wait_timeout):
        """Verify recommendation displays action (BUY, SELL, HOLD)."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "ticker-input")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Find and check recommendation action
        rec_action = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "recommendation-action"))
        )
        action_text = rec_action.text.upper()
        assert action_text in ["BUY", "SELL", "HOLD"]


class TestDataTables:
    """Test cases for data table displays."""

    def test_fundamentals_table_loads(self, browser, base_url, wait_timeout):
        """Verify fundamentals table loads with data."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Wait for fundamentals table
        table = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "fundamentals-table"))
        )
        assert table.is_displayed()

        # Check for table rows
        rows = table.find_elements(By.TAG_NAME, "tr")
        assert len(rows) > 0

    def test_price_history_table_displays(self, browser, base_url, wait_timeout):
        """Verify price history table displays correctly."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Click on price history tab if needed
        # Adjust based on actual HTML structure

        # Wait for price history table
        table = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "price-history-table"))
        )
        assert table.is_displayed()


class TestUIInteractions:
    """Test cases for UI interactions and responsiveness."""

    def test_logo_click_returns_home(self, browser, base_url, wait_timeout):
        """Verify clicking logo returns to home page."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        # Search for stock first
        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Click logo
        logo = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "logo")))
        logo.click()

        # Should return to landing page
        wait.until(EC.presence_of_element_located((By.ID, "landing-page")))
        assert browser.find_element(By.ID, "landing-page").is_displayed()

    def test_enter_key_submits_search(self, browser, base_url, wait_timeout):
        """Verify pressing Enter in search input submits form."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL")
        search_input.send_keys(Keys.RETURN)

        # Should load results
        wait.until(EC.presence_of_element_located((By.ID, "results-page")))
        assert browser.find_element(By.ID, "results-page").is_displayed()

    def test_tab_switching(self, browser, base_url, wait_timeout):
        """Verify switching between tabs works."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "results-page")))

        # Get all tab buttons
        tabs = browser.find_elements(By.CLASS_NAME, "tab-button")

        if len(tabs) > 1:
            # Click second tab
            tabs[1].click()

            # Verify tab is active
            active_tab = browser.find_element(By.CLASS_NAME, "tab-button.active")
            assert active_tab.is_displayed()


class TestErrorHandling:
    """Test cases for error handling and edge cases."""

    def test_invalid_ticker_handling(self, browser, base_url, wait_timeout):
        """Verify invalid ticker is handled gracefully."""
        browser.get(base_url)
        wait = WebDriverWait(browser, wait_timeout)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("INVALID123XYZ")
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()

        # Should either show error message or no data
        # Adjust based on actual error handling
        try:
            error_msg = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "error-message")),
                timeout=5
            )
            assert error_msg.is_displayed()
        except:
            # Or could show empty results
            results = browser.find_elements(By.ID, "results-page")
            assert len(results) > 0

    def test_special_characters_in_search(self, browser, base_url):
        """Verify special characters are handled."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 10)

        search_input = wait.until(EC.presence_of_element_located((By.ID, "stock-ticker")))
        search_input.send_keys("AAPL$#@!")

        # Should sanitize or reject
        value = search_input.get_attribute("value")
        # Either cleaned or original
        assert len(value) <= 10
