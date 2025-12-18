#!/usr/bin/env python3
"""
Manual test script: Screen undervalued stocks and get AI action recommendations.

Usage: python test_manual_screening.py [BASE_URL]
Example: python test_manual_screening.py http://192.168.1.248:8000
"""

import sys
import json
import urllib.request
import urllib.error
from urllib.parse import urljoin

def get_base_url(provided_url=None):
    """Determine the base URL, with fallback to localhost if needed."""
    if provided_url:
        return provided_url
    
    base_url = "http://192.168.1.248:8000"
    
    # Try the default URL
    try:
        urllib.request.urlopen(base_url + "/", timeout=3)
        return base_url
    except Exception:
        pass
    
    # Fallback to localhost
    alt_url = "http://localhost:8000"
    try:
        urllib.request.urlopen(alt_url + "/", timeout=3)
        return alt_url
    except Exception:
        return base_url


def fetch_json(url):
    """Fetch JSON from a URL."""
    timeout = 480  # 8 minutes
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise Exception(f"HTTP {e.code}: {e.reason}")
    except Exception as e:
        raise Exception(f"Failed to fetch {url}: {e}")


def get_undervalued_stocks(base_url):
    """Fetch list of undervalued stocks from the screening endpoint."""
    url = urljoin(base_url, "/api/screen-undervalued")
    return fetch_json(url)


def get_ai_recommendation(base_url, ticker):
    """Get AI action recommendation word for a given ticker."""
    url = urljoin(base_url, f"/api/ai/action-recommendation-word/{ticker}")
    recommendation = fetch_json(url)
    
    # Clean up - remove quotes if present
    if isinstance(recommendation, str):
        recommendation = recommendation.strip('"')
    
    return recommendation


def main():
    # Get base URL from command line or use default
    base_url = get_base_url(sys.argv[1] if len(sys.argv) > 1 else None)
    
    print(f"Screening undervalued stocks at: {base_url}")
    print()
    
    # Fetch undervalued stocks
    print("Fetching undervalued stocks...")
    try:
        tickers = get_undervalued_stocks(base_url)
    except Exception as e:
        print(f"Error: Could not fetch undervalued stocks: {e}")
        sys.exit(1)
    
    if not tickers:
        print("Error: No tickers returned from screen-undervalued endpoint")
        sys.exit(1)
    
    print(f"Found {len(tickers)} undervalued stocks")
    print("Getting AI recommendations...")
    print()
    
    # Print header
    print("TICKER,RECOMMENDATION")
    
    # Get recommendations for each ticker
    for ticker in tickers:
        try:
            recommendation = get_ai_recommendation(base_url, ticker)
            print(f"{ticker},{recommendation}")
        except Exception as e:
            print(f"{ticker},ERROR: {e}")


if __name__ == "__main__":
    main()
