#!/usr/bin/env bash
# Simple tester for data API endpoints
# Usage: ./test_data_endpoints.sh [BASE_URL]
# Example: ./test_data_endpoints.sh http://localhost:8000

BASE_URL="${1:-http://192.168.1.248:8000}"
SYMBOL="AAPL"

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
  # Print raw body only (no parsing)
  curl -sS "$BASE_URL$path" || true
  echo
  echo
}

# Data Endpoints (9)
request "/api/fundamentals/$SYMBOL"
request "/api/price-history/$SYMBOL"
request "/api/analyst-targets/$SYMBOL"
request "/api/calendar/$SYMBOL"
request "/api/income-stmt/$SYMBOL"
request "/api/balance-sheet/$SYMBOL"
request "/api/option-chain/$SYMBOL"
request "/api/news/$SYMBOL"
request "/api/screen-undervalued"
