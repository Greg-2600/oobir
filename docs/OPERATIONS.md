# OOBIR Operations Guide

This is the operational reference for the Docker Compose stack and the Python
processes it runs. It covers the published ports, environment variables, cache
and data paths, and the `daily-sync` container. Every value below comes from
`docker-compose.yml`, the `Dockerfile`, or the application code.

## Services and ports

| Compose service | Container | Host port | Container port | Role |
| --------------- | --------- | --------- | -------------- | ---- |
| `web` | `oobir_web` | `2009` | `80` | Nginx static UI and reverse proxy |
| `app` | `oobir_app` | `2010` | `2009` | FastAPI application |
| `oobir_ollama` | `oobir_ollama` | `11436` | `11434` | Local Ollama model server |
| `postgres` | `oobir_postgres` | `5432` | `5432` | TimescaleDB/PostgreSQL |
| `daily-sync` | `oobir_daily_sync` | none | none | Weekday data sync scheduler |

The API container listens on `2009` because the `Dockerfile` runs Uvicorn with
`--port 2009` and exposes that port. Compose publishes it on host port `2010`.
The web container serves the UI on host port `2009`; its Nginx configuration
proxies `/api/`, `/docs`, `/openapi.json`, and `/redoc` to the API at
`172.24.0.2:2009`.

When running the API directly instead of through Compose, `python flow_api.py`
uses `HOST` and `PORT` from the environment. The code defaults are
`127.0.0.1:8000`. The Docker command does not use these variables; it always
starts Uvicorn on `0.0.0.0:2009`.

## Environment variables

### API and authentication

| Variable | Used by | Behaviour |
| -------- | ------- | --------- |
| `OOBIR_API_KEYS` | `flow_api.py` | Comma-separated list of accepted keys. If unset or empty, the API uses a built-in development key. Compose supplies a development default when the variable is unset. |
| `OOBIR_AUTH_ENABLED` | `flow_api.py` | Defaults to enabled. Set to `false` to disable key checks. When enabled, requests to `/api/*` require the `X-API-Key` header, except `/api/health*` and `/api/cache*`. |
| `OOBIR_CORS_ORIGINS` | `flow_api.py` | Comma-separated list of origins allowed by CORS, for example `https://ui.example.com,https://admin.example.com`. Whitespace around entries is trimmed and empty entries are ignored. If unset or empty, the built-in local and LAN origin list is used unchanged. Setting `*` allows any origin and automatically turns off credentialed CORS requests. |
| `OLLAMA_HOST` | `flow.py`, `flow_api.py` | Ollama base URL. Code default is `http://ollama:11434`; the `Dockerfile` sets `http://oobir_ollama:11434`; Compose overrides it for the app with `http://ollama:11434`. |
| `HOST` | `flow_api.py` (`__main__`) | Bind address for a direct `python flow_api.py` run. Default `127.0.0.1`. |
| `PORT` | `flow_api.py` (`__main__`) | Bind port for a direct `python flow_api.py` run. Default `8000`. |

Never commit API key values. Supply `OOBIR_API_KEYS` through the environment or
your deployment secret store.

Browsers reject `Access-Control-Allow-Origin: *` together with credentials, so
a wildcard in `OOBIR_CORS_ORIGINS` disables `allow_credentials`. Use explicit
origins for clients that send cookies or `Authorization` headers.

`flow.py` also derives `OLLAMA_URL` and `OLLAMA_BASE_URL` from the selected
Ollama host so the Ollama client sees a consistent setting.

### Ollama container

| Variable | Set in | Purpose |
| -------- | ------ | ------- |
| `OLLAMA_ALLOW_HTTP` | `docker-compose.yml` | Allows plain HTTP for the Ollama server. |
| `OLLAMA_CONTEXT_SIZE` | `docker-compose.yml` | Sets the model context window. |
| `OLLAMA_HOST` | `docker-compose.yml`, `Dockerfile` | Address the app uses to reach Ollama. |
| `OLLAMA_MODEL` | `docker-compose.yml` | Declared for the app service. The Python code currently uses a hard-coded model identifier in `flow.py`, so changing this variable alone does not change inference. |

### PostgreSQL and TimescaleDB

These variables are read by `db_timescale.py` and the scripts under `scripts/`.

| Variable | Default in code | Purpose |
| -------- | --------------- | ------- |
| `PGHOST` | `localhost` | Database host. Compose sets `postgres` for the app and daily-sync services. |
| `PGPORT` | `5432` | Database port. |
| `PGDATABASE` | `oobir` | Database name. |
| `PGUSER` | `oobir` | Database user. |
| `PGPASSWORD` | development value | Database password. Compose supplies a development value. |

The `postgres` container itself is configured with `POSTGRES_DB`,
`POSTGRES_USER`, and `POSTGRES_PASSWORD` in `docker-compose.yml`.

### Daily sync scheduler

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `SYNC_HOUR` | `18` | Hour (0-23) for the weekday run. |
| `SYNC_MINUTE` | `0` | Minute (0-59) for the weekday run. |
| `TZ` | system default | Timezone for the schedule. Compose sets `America/New_York`. |
| `SYNC_ON_STARTUP` | `0` | Set to `1` to run a sync immediately when the container starts. |

### Historical data bootstrap

`scripts/bootstrap_db_data.sh` accepts these optional environment variables:

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `BATCH_SIZE` | `50` | Number of tickers per fetch invocation. |
| `APP_SERVICE` | `app` | Compose service used for the fetch/load steps. |
| `POSTGRES_SERVICE` | `postgres` | Compose service used for verification queries. |

### Machine learning

ML settings use the `OOOBIR_ML_*` prefix and are read in `ml/config.py`.

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `OOOBIR_ML_HORIZON` | `5` | Forward-return horizon in trading days. |
| `OOOBIR_ML_MARGIN` | `0.0` | Symmetric dead-band treated as `FLAT`. |
| `OOOBIR_ML_WINDOW` | `250` | Trailing feature window. |
| `OOOBIR_ML_MIN_HISTORY` | `120` | Minimum history rows for a prediction. |
| `OOOBIR_ML_MODEL_DIR` | `models/` under the current working directory | Model artifact directory. |
| `OOOBIR_ML_ENABLE` | `0` | Master switch for broader ML surfacing. |
| `OOOBIR_ML_BT_MIN_TRAIN` | `60` | Minimum walk-forward training rows. |
| `OOOBIR_ML_BT_FOLDS` | `3` | Default walk-forward folds. |
| `OOOBIR_ML_BT_MAX_TRAIN` | `200` | Cap on each fold's training window. |

## Cache and data paths

| Path | Location | Notes |
| ---- | -------- | ----- |
| SQLite response cache | `cache.db` beside `db.py`; in the app container `/home/app/oobir/cache.db` | Auto-created by `db.py`, gitignored, with a 500-entry in-memory LRU in front of it. Compose does not mount it as a volume. |
| ML model artifacts | `OOOBIR_ML_MODEL_DIR`, default `models/` under the working directory | `model.joblib` and `meta.json`; gitignored and not mounted by Compose. |
| Historical data staging | `historical_data/` at the repository root | Used by the fetch/load scripts; gitignored and excluded from the Docker build context. |
| Ollama models | Named volume `ollama_data` mounted at `/var/lib/ollama` | Persists downloaded models. |
| PostgreSQL data | Named volume `postgres_data` mounted at `/var/lib/postgresql/data` | Persists database contents. |
| Database init scripts | Bind mount `./db/init` at `/docker-entrypoint-initdb.d` | Run by the Postgres image on first initialization. |
| Web assets | Bind mount `./web` at `/usr/share/nginx/html` | Served by Nginx. |
| Nginx configuration | Bind mount `./web/nginx.conf` at `/etc/nginx/conf.d/default.conf` (read-only) | Reverse-proxy and cache-header rules. |

Because the SQLite cache, ML artifacts, and historical data are not named
volumes, they do not survive container removal unless you add a bind mount or
named volume for them.

## Daily sync container

The `daily-sync` service uses the same image as `app`, runs
`python scripts/daily_sync_scheduler.py`, depends on `postgres`, and restarts
unless stopped. It publishes no ports. The scheduler runs weekdays at the
configured `SYNC_HOUR`/`SYNC_MINUTE` in the configured `TZ` and skips weekends.

Each run calls `scripts/daily_sync.py`, which:

- Fetches end-of-day prices and back-fills gaps.
- Refreshes fundamentals.
- Recomputes technical indicators.

Manual runs from the host:

```bash
# Sync all tracked tickers
docker compose exec daily-sync python scripts/daily_sync.py

# Sync specific tickers only
docker compose exec daily-sync python scripts/daily_sync.py AAPL MSFT TSLA

# Prices only or fundamentals only
docker compose exec daily-sync python scripts/daily_sync.py --prices-only
docker compose exec daily-sync python scripts/daily_sync.py --fundamentals-only
```

The service reads the `PG*` variables listed above. It does not need an API key
or access to Ollama.

## Related documentation

- [README](../README.md) for quick start and feature overview.
- [ML_PREDICTIONS.md](ML_PREDICTIONS.md) for the ML pipeline and model lab.
- [MARKET_BRIEFING.md](MARKET_BRIEFING.md) for the market briefing dashboard.
