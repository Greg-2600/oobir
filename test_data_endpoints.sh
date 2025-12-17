#!/usr/bin/env bash
set -euo pipefail

# Simple tester for data API endpoints
# Usage: ./test_data_endpoints.sh [BASE_URL] [SYMBOL]
# Example: ./test_data_endpoints.sh http://localhost:8000 AAPL

BASE_URL="${1:-http://192.168.1.248:8000}"
SYMBOL="${2:-AAPL}"

# If default URL fails and no arg provided, try localhost
if [[ -z "$1" ]]; then
  if ! curl -sS --max-time 3 "$BASE_URL/" >/dev/null 2>&1; then
    ALT="http://localhost:8000"
    if curl -sS --max-time 3 "$ALT/" >/dev/null 2>&1; then
      BASE_URL="$ALT"
    fi
  fi
fi

echo "Testing data endpoints at: $BASE_URL"
echo "Using symbol: $SYMBOL"
echo

request() {
  local path="$1"
  echo "=== GET $BASE_URL$path ==="
  curl -sS -w "\nHTTP_STATUS:%{http_code}\n" "$BASE_URL$path" || true
  echo
}

# Data Endpoints
echo "Testing ${SYMBOL:-AAPL} fundamentals..."
request "/api/fundamentals/$SYMBOL"
request "/api/price-history/$SYMBOL"
request "/api/analyst-targets/$SYMBOL"
request "/api/calendar/$SYMBOL"

echo "Testing ${SYMBOL} financial statements..."
request "/api/income-stmt/$SYMBOL"
request "/api/balance-sheet/$SYMBOL"
request "/api/option-chain/$SYMBOL"

echo "Testing ${SYMBOL} news and screening..."
request "/api/news/$SYMBOL"
request "/api/screen-undervalued"
