"""
Pytest configuration and fixtures for Selenium UI tests.
"""
import os
import shutil
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


# Determine which browsers to run. Default to chrome (headless) for CI.
env_browsers = os.getenv("UI_BROWSERS")
if env_browsers:
    _requested = [b.strip().lower() for b in env_browsers.split(",") if b.strip()]
else:
    _requested = ["chrome"]

# Detect available browser binaries; skip tests at import-time if none present.
_available = []
for b in _requested:
    if b == "chrome":
        if shutil.which("google-chrome") or shutil.which("chrome") or shutil.which("chromium") or shutil.which("chromium-browser"):
            _available.append("chrome")
    elif b == "firefox":
        if shutil.which("firefox"):
            _available.append("firefox")

if not _available:
    pytest.skip("No Chrome/Firefox binary found on PATH; skipping UI tests.", allow_module_level=True)


@pytest.fixture(params=_available)
def browser(request):
    """Provide a browser instance. Runs headless by default (can be controlled
    with environment variable `HEADLESS=0`). Use `UI_BROWSERS` to customize
    which browsers to attempt (comma-separated, e.g. "chrome,firefox").
    """
    browser_name = request.param
    driver = None
    headless = os.getenv("HEADLESS", "1") not in ("0", "false", "False")

    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if headless:
            # Use new headless mode when available
            options.add_argument("--headless=new")
        else:
            options.add_argument("--start-maximized")
        try:
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options
            )
        except Exception as e:
            pytest.skip(f"Could not start chrome driver: {e}")

    elif browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("-headless")
        else:
            options.add_argument("--start-maximized")
        try:
            driver = webdriver.Firefox(
                service=FirefoxService(GeckoDriverManager().install()),
                options=options
            )
        except Exception as e:
            pytest.skip(f"Could not start firefox driver: {e}")

    yield driver

    if driver:
        try:
            driver.quit()
        except Exception:
            pass


@pytest.fixture
def base_url():
    """Base URL for the application. Override with BASE_URL env var."""
    return os.getenv("BASE_URL", "http://localhost:8081")


@pytest.fixture
def wait_timeout():
    """Default wait timeout in seconds for Selenium waits."""
    return int(os.getenv("WAIT_TIMEOUT", "10"))
