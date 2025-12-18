#!/usr/bin/env bash
set -euo pipefail

# Usage: ./test_ai_endpoints.sh [BASE_URL] [SYMBOL]
# Example: ./test_ai_endpoints.sh http://192.168.1.248:8000 CHTR

BASE_URL="${1:-http://192.168.1.248:8000}"
SYMBOL="${2:-CHTR}"

# If default URL fails and no arg provided, try localhost
if [[ -z "${1:-}" ]]; then
  if ! curl -sS --max-time 3 "$BASE_URL/" >/dev/null 2>&1; then
    ALT="http://localhost:8000"
    if curl -sS --max-time 3 "$ALT/" >/dev/null 2>&1; then
      BASE_URL="$ALT"
    fi
  fi
fi

echo "Testing AI endpoints at: $BASE_URL"
echo "Using symbol: $SYMBOL"
echo

request() {
  local path="$1"
  echo "=== GET $BASE_URL$path ==="
  curl -sS -w "\nHTTP_STATUS:%{http_code}\n" "$BASE_URL$path" || true
  echo
}

# AI Analysis Endpoints
echo "Testing AI analysis endpoints for ${SYMBOL}..."
request "/api/ai/fundamental-analysis/$SYMBOL"
request "/api/ai/technical-analysis/$SYMBOL"

echo "Testing AI recommendation endpoints for ${SYMBOL}..."
request "/api/ai/action-recommendation/$SYMBOL"
request "/api/ai/action-recommendation-sentence/$SYMBOL"
request "/api/ai/action-recommendation-word/$SYMBOL"
