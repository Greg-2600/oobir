"""
Pytest configuration and fixtures for Selenium UI tests.
"""
import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


@pytest.fixture(params=["chrome", "firefox"])
def browser(request):
    """
    Fixture that provides browser instances for both Chrome and Firefox.
    Tests using this fixture will run against both browsers.
    """
    browser_name = request.param
    driver = None

    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # Uncomment for headless mode in CI/CD:
        # options.add_argument("--headless")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
    elif browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        options.add_argument("--start-maximized")
        # Uncomment for headless mode in CI/CD:
        # options.add_argument("--headless")
        driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=options
        )

    yield driver

    if driver:
        driver.quit()


@pytest.fixture
def base_url():
    """Base URL for the application. Override with BASE_URL env var."""
    return os.getenv("BASE_URL", "http://localhost:8081")


@pytest.fixture
def wait_timeout():
    """Default wait timeout in seconds for Selenium waits."""
    return int(os.getenv("WAIT_TIMEOUT", "10"))
