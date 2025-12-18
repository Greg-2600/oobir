#!/bin/bash
# Simple git workflow for creating news_improvements branch
# Run this to set up the branch with all changes

set -e

echo "Creating news_improvements branch..."
git checkout -b news_improvements || git checkout news_improvements

echo "Staging modified files..."
git add flow.py
git add flow_api.py
git add tests/test_news_sentiment.py
git add tests/test_api_news_sentiment.py
git add DOCS.md
git add NEWS_SENTIMENT.md
git add CHANGELOG_NEWS_SENTIMENT.md

echo "Checking status..."
git status

echo ""
echo "Ready to commit. To commit, run:"
echo "  git commit -m 'Add news sentiment analysis feature'"
echo ""
echo "To push to GitHub, run:"
echo "  git push -u origin news_improvements"
