#!/usr/bin/env bash
set -euo pipefail

# Bootstrap market data into Postgres after containers are running.
#
# Usage:
#   scripts/bootstrap_db_data.sh
#   scripts/bootstrap_db_data.sh sp500_tickers.txt
#
# Optional env vars:
#   BATCH_SIZE=50              Number of tickers per fetch invocation.
#   APP_SERVICE=app            Docker Compose service name for the app container.
#   POSTGRES_SERVICE=postgres  Docker Compose service name for the Postgres container.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

TICKER_FILE="${1:-sp500_tickers.txt}"
BATCH_SIZE="${BATCH_SIZE:-50}"
APP_SERVICE="${APP_SERVICE:-app}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"

if [[ ! -f "${TICKER_FILE}" ]]; then
  echo "Ticker file not found: ${TICKER_FILE}" >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Neither 'docker compose' nor 'docker-compose' is available." >&2
  exit 1
fi

echo "Using compose command: ${COMPOSE_CMD[*]}"
echo "Ticker file: ${TICKER_FILE}"
echo "Batch size: ${BATCH_SIZE}"

# Sanity check that target services are reachable.
"${COMPOSE_CMD[@]}" exec -T "${APP_SERVICE}" true
"${COMPOSE_CMD[@]}" exec -T "${POSTGRES_SERVICE}" true

echo "Starting fetch + load pipeline..."
"${COMPOSE_CMD[@]}" exec -T \
  -e TICKER_FILE="${TICKER_FILE}" \
  -e BATCH_SIZE="${BATCH_SIZE}" \
  "${APP_SERVICE}" bash -lc '
    set -euo pipefail

    xargs -a "$TICKER_FILE" -n "$BATCH_SIZE" python scripts/fetch_historical_price.py
    xargs -a "$TICKER_FILE" -n "$BATCH_SIZE" python scripts/fetch_fundamentals.py

    echo "Price JSON files: $(ls historical_data/*_price_history_all.json 2>/dev/null | wc -l)"
    echo "Fund JSON files:  $(ls historical_data/*_fundamentals.json 2>/dev/null | wc -l)"

    python scripts/load_historical_data.py
    python scripts/load_fundamentals.py
  '

echo "Verifying database counts..."
"${COMPOSE_CMD[@]}" exec -T "${POSTGRES_SERVICE}" psql -U oobir -d oobir -c '
SELECT COUNT(DISTINCT ticker) AS price_tickers FROM price_history;
SELECT COUNT(DISTINCT ticker) AS fundamentals_tickers FROM fundamentals;
'

echo "Bootstrap complete."
