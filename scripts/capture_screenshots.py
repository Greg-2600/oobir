#!/usr/bin/env python3
"""Capture screenshots of the OOBIR web UI for README documentation."""

import time
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = "docs/screenshots"
BASE_URL = "http://localhost:8081"


def capture_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # 1. Landing page / search page
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path=f"{SCREENSHOTS_DIR}/01_landing_page.png", full_page=False)
        print("✓ Landing page captured")

        # 2. Search for AAPL to load stock data
        search_input = page.locator('input[type="text"]').first
        search_input.fill("AAPL")
        search_input.press("Enter")

        # Wait for data to load
        time.sleep(8)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # 3. Stock overview - top section with chart
        page.screenshot(
            path=f"{SCREENSHOTS_DIR}/02_stock_overview.png", full_page=False
        )
        print("✓ Stock overview captured")

        # 4. Full page with all data cards
        page.screenshot(
            path=f"{SCREENSHOTS_DIR}/03_stock_full_page.png", full_page=True
        )
        print("✓ Full stock page captured")

        # 5. Scroll down to see fundamentals and data cards
        page.evaluate("window.scrollBy(0, 900)")
        time.sleep(1)
        page.screenshot(
            path=f"{SCREENSHOTS_DIR}/04_fundamentals_data.png", full_page=False
        )
        print("✓ Fundamentals data captured")

        # 6. Try the API docs page
        page2 = browser.new_page(viewport={"width": 1400, "height": 900})
        page2.goto("http://localhost:8000/docs")
        page2.wait_for_load_state("networkidle")
        time.sleep(2)
        page2.screenshot(path=f"{SCREENSHOTS_DIR}/05_api_docs.png", full_page=False)
        print("✓ API docs captured")
        page2.close()

        # 7. Check for stocks/markets pages
        try:
            page3 = browser.new_page(viewport={"width": 1400, "height": 900})
            page3.goto(f"{BASE_URL}/stocks.html")
            page3.wait_for_load_state("networkidle")
            time.sleep(3)
            page3.screenshot(
                path=f"{SCREENSHOTS_DIR}/06_stock_screener.png", full_page=False
            )
            print("✓ Stock screener captured")
            page3.close()
        except Exception as e:
            print(f"  Skipped stock screener: {e}")

        browser.close()
        print(f"\nAll screenshots saved to {SCREENSHOTS_DIR}/")


if __name__ == "__main__":
    capture_screenshots()
