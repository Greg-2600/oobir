"""
UI Validation Tests - Run with Selenium when browser is available.

These tests validate the UI renders correctly with expected styles.
Run from project root:
    BASE_URL=http://192.168.1.248:2009 python3 -m pytest tests/ui/test_ui_validation.py -v
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestLandingPageStyling:
    """Validate the landing page has correct styling applied."""

    def test_page_has_correct_background_color(self, browser, base_url):
        """Page background should be light gray (#f8fafc), not gradient."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        bg_color = browser.execute_script(
            "return window.getComputedStyle(document.querySelector('.unified-page')).backgroundColor;"
        )
        rgb_to_hex = lambda r, g, b: f"#{r:02x}{g:02x}{b:02x}"
        if bg_color.startswith("rgb("):
            parts = bg_color.replace("rgb(", "").replace(")", "").split(",")
            bg_color = rgb_to_hex(int(parts[0]), int(parts[1]), int(parts[2]))

        assert "f8fafc" in bg_color.lower() or "rgb(248, 250, 252)" in bg_color, \
            f"Expected light gray background, got: {bg_color}"

    def test_header_is_white_with_border(self, browser, base_url):
        """Header should be white with bottom border."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        header_bg = browser.execute_script(
            "return window.getComputedStyle(document.querySelector('.unified-header')).backgroundColor;"
        )
        header_border = browser.execute_script(
            "return window.getComputedStyle(document.querySelector('.unified-header')).borderBottomColor;"
        )

        import re
        def rgb_to_hex(rgb):
            if not rgb.startswith("rgb"): return rgb
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb)
            if match:
                return f"#{int(match.group(1)):02x}{int(match.group(2)):02x}{int(match.group(3)):02x}"
            return rgb

        header_bg = rgb_to_hex(header_bg)
        header_border = rgb_to_hex(header_border)

        assert "ffffff" in header_bg.lower(), f"Expected white header, got: {header_bg}"
        assert "e5e7eb" in header_border.lower(), f"Expected light border, got: {header_border}"

    def test_logo_has_correct_styling(self, browser, base_url):
        """Logo should have bold blue styling with red accent."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        logo = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "unified-logo")))

        font_weight = browser.execute_script(
            "return window.getComputedStyle(arguments[0]).fontWeight;", logo
        )
        color = browser.execute_script(
            "return window.getComputedStyle(arguments[0]).color;", logo
        )

        import re
        def rgb_to_hex(rgb):
            if not rgb.startswith("rgb"): return rgb
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb)
            if match:
                return f"#{int(match.group(1)):02x}{int(match.group(2)):02x}{int(match.group(3)):02x}"
            return rgb

        color = rgb_to_hex(color)

        assert int(font_weight) >= 700, f"Expected bold logo, got weight: {font_weight}"
        assert "1a73e8" in color.lower(), f"Expected blue logo color, got: {color}"

    def test_nav_pills_are_compact(self, browser, base_url):
        """Nav items should be compact pills with small font."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        nav_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".unified-nav a")))

        for link in nav_links[:3]:
            font_size = browser.execute_script(
                "return window.getComputedStyle(arguments[0]).fontSize;", link
            )
            padding = browser.execute_script(
                "return window.getComputedStyle(arguments[0]).padding;", link
            )

            font_size_px = int(font_size.replace("px", ""))
            assert font_size_px <= 14, f"Expected small font, got: {font_size}"

            if "padding" in padding:
                first_padding = int(padding.split()[0].replace("px", ""))
                assert first_padding <= 14, f"Expected compact padding, got: {padding}"

    def test_stocks_grid_exists(self, browser, base_url):
        """Stocks grid section should exist and be visible."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        grid = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "stocks-grid")))
        assert grid.is_displayed()

    def test_market_radar_exists(self, browser, base_url):
        """Market radar section should exist."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        radar = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "market-radar-section")))
        assert radar.is_displayed()

    def test_no_radial_gradients_on_body(self, browser, base_url):
        """Body should NOT have radial gradients (old yellow style)."""
        browser.get(base_url)
        wait = WebDriverWait(browser, 15)

        body_bg = browser.execute_script(
            "return window.getComputedStyle(document.body).backgroundImage;"
        )

        assert "radial-gradient" not in body_bg.lower(), \
            f"Found radial gradient on body - old style not removed: {body_bg[:100]}"


class TestStockDetailPage:
    """Validate stock detail page renders correctly."""

    def test_results_page_loads(self, browser, base_url):
        """Stock detail page should load via ticker URL."""
        browser.get(f"{base_url}/?ticker=AAPL")
        wait = WebDriverWait(browser, 30)

        results = wait.until(EC.presence_of_element_located((By.ID, "results-page")))
        assert results.is_displayed()

    def test_fundamentals_section_exists(self, browser, base_url):
        """Fundamentals section should exist."""
        browser.get(f"{base_url}/?ticker=AAPL")
        wait = WebDriverWait(browser, 30)

        wait.until(lambda d: "hidden" not in d.find_element(By.ID, "results-container").get_attribute("class"))

        fundamentals = wait.until(EC.presence_of_element_located((By.ID, "fundamentals-data")))
        assert fundamentals is not None


class TestNavigation:
    """Validate navigation across pages."""

    @pytest.mark.parametrize("page", [
        "index.html",
        "search.html",
        "stocks.html",
        "money-flow.html",
        "markets.html",
    ])
    def test_all_pages_have_consistent_nav(self, browser, base_url, page):
        """All pages should have consistent navigation with 10 links in correct order."""
        browser.get(f"{base_url}/{page}")
        wait = WebDriverWait(browser, 15)

        nav_links = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".app-nav a"))
        )

        expected_pages = [
            "search.html", "index.html", "screener.html", "markets.html",
            "stocks.html", "predictions.html", "money-flow.html",
            "crypto.html", "metals.html", "commodities.html"
        ]

        hrefs = [link.get_attribute("href", "").split("/")[-1] for link in nav_links]
        assert len(hrefs) == 10, f"Expected 10 nav links, got {len(hrefs)}: {hrefs}"
        assert hrefs == expected_pages, f"Nav order incorrect. Got: {hrefs}"


class TestMoneyFlowPage:
    """Validate money flow page works for all periods."""

    @pytest.mark.parametrize("period", [
        ("day", "today"),
        ("week", "week"),
        ("month", "month"),
        ("3month", "3 months"),
        ("6month", "6 months"),
        ("year", "year"),
    ])
    def test_money_flow_periods(self, browser, base_url, period):
        """Money flow should work for all time periods."""
        period_val, period_name = period
        browser.get(f"{base_url}/money-flow.html")
        wait = WebDriverWait(browser, 20)

        select = wait.until(EC.presence_of_element_located((By.ID, "period-select")))
        select.click()

        option = browser.find_element(By.CSS_SELECTOR, f"#period-select option[value='{period_val}']")
        option.click()

        browser.find_element(By.ID, "tab-in").click()

        import time
        time.sleep(3)

        cards = browser.find_elements(By.CLASS_NAME, "money-flow-card")
        assert len(cards) > 0, f"No money flow cards for period {period_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
