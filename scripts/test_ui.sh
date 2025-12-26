#!/bin/bash
# Run Selenium UI tests
# Usage: ./scripts/test_ui.sh [BASE_URL] [BROWSERS]
# Examples:
#   ./scripts/test_ui.sh
#   ./scripts/test_ui.sh http://192.168.1.175:8082
#   ./scripts/test_ui.sh http://localhost:8081 "chrome"

set -e

# Configuration
BASE_URL="${1:-http://localhost:8081}"
BROWSERS="${2:-chrome,firefox}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-10}"

echo "=========================================="
echo "OOBIR Selenium UI Test Suite"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Browsers: $BROWSERS"
echo "Wait Timeout: ${WAIT_TIMEOUT}s"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dev requirements..."
    pip install -r dev-requirements.txt
fi

# Run tests
echo "Starting tests..."
BASE_URL="$BASE_URL" WAIT_TIMEOUT="$WAIT_TIMEOUT" pytest tests/ui/ -v --tb=short

echo ""
echo "✅ UI tests completed!"
