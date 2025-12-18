#!/usr/bin/env python3
"""Test the news sentiment analysis function."""

import flow

# Test the new function
ticker = "CHTR"
print(f"Testing news sentiment analysis for {ticker}...")
print("=" * 80)

result = flow.get_ai_news_sentiment(ticker)
print(f"\nNews Sentiment for {ticker}:")
print(result)
print("=" * 80)
