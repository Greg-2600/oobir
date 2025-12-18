#!/usr/bin/env python3
"""
Fetch undervalued tickers, then sequentially get AI recommendation words per ticker.

Usage:
  python screen_undervalued_recommendations.py [BASE_URL]

Examples:
  python screen_undervalued_recommendations.py
  python screen_undervalued_recommendations.py http://localhost:8000
  python screen_undervalued_recommendations.py http://192.168.1.248:8000
"""

import sys
import time
import requests
from urllib.parse import urljoin

DEFAULT_URLS = [
    "http://192.168.1.248:8000",
    "http://localhost:8000",
]

TIMEOUT_SECONDS = 600  # allow up to 10 minutes per request
MAX_RETRIES = 3  # retry failed requests up to 3 times
RETRY_DELAY = 2  # wait 2 seconds between retries


def pick_base_url(cli_url: str | None) -> str:
    """Return a reachable base URL, preferring CLI arg, else defaults."""
    # If user provided a URL, try it first
    if cli_url:
        if is_reachable(cli_url):
            return cli_url
        # fall through to defaults if not reachable

    # Try known defaults
    for candidate in DEFAULT_URLS:
        if is_reachable(candidate):
            return candidate

    # If none reachable, return CLI or first default so user sees an error from requests
    return cli_url or DEFAULT_URLS[0]


def is_reachable(base_url: str) -> bool:
    try:
        r = requests.get(urljoin(base_url, "/"), timeout=3)
        return r.ok
    except Exception:
        return False


def get_undervalued_tickers(base_url: str) -> list:
    """GET /api/screen-undervalued -> list of tickers."""
    url = urljoin(base_url, "/api/screen-undervalued")
    r = requests.get(url, timeout=TIMEOUT_SECONDS)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response for screen-undervalued: {data!r}")
    return data


def get_technical_analysis(base_url: str, ticker: str) -> str:
    """GET /api/ai/technical-analysis/{ticker} -> AI technical analysis text.
    Handles both JSON and raw-string responses. Retries on failure.
    """
    url = urljoin(base_url, f"/api/ai/technical-analysis/{ticker}")
    
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=TIMEOUT_SECONDS)
            r.raise_for_status()

            # Prefer JSON if available; fallback to raw text
            try:
                data = r.json()
                if isinstance(data, str):
                    return data.strip().strip('"')
                # If server wraps into {"word": "BUY"}, try common keys
                for key in ("word", "recommendation", "result"):
                    if key in data and isinstance(data[key], str):
                        return data[key].strip().strip('"')
                # Otherwise coerce to string
                return str(data).strip().strip('"')
            except ValueError:
                # Not JSON; use text
                return r.text.strip().strip('"')
        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt < MAX_RETRIES - 1:
                print(f"  {ticker}: Timeout/connection error (attempt {attempt + 1}/{MAX_RETRIES}), retrying in {RETRY_DELAY}s...", file=sys.stderr)
                time.sleep(RETRY_DELAY)
            else:
                raise Exception(f"Timeout after {MAX_RETRIES} attempts: {exc}") from exc
        except Exception as exc:
            raise exc


def main(argv: list[str]) -> int:
    base_url = pick_base_url(argv[1] if len(argv) > 1 else None)
    print(f"Using API base: {base_url}\n")

    # 1) Undervalued tickers
    print("Fetching undervalued tickers...")
    try:
        tickers = get_undervalued_tickers(base_url)
    except Exception as exc:
        print(f"Error: failed to fetch undervalued tickers: {exc}")
        return 1

    if not tickers:
        print("No tickers returned from screen-undervalued endpoint")
        return 1

    print(f"Found {len(tickers)} tickers. Getting technical analysis...\n")

    # 2) Sequentially get technical analysis per ticker
    print("=" * 80)
    for ticker in tickers:
        try:
            analysis = get_technical_analysis(base_url, ticker)
            print(f"\n{ticker}:\n{analysis}")
            print("=" * 80)
        except Exception as exc:
            print(f"\n{ticker}: ERROR: {exc}")
            print("=" * 80)
        # Optional tiny delay to be kind to the server
        time.sleep(0.05)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
