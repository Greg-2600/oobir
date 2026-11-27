# OOBIR Roadmap

## Vision

OOBIR aims to be a practical, self contained stock research platform that combines a FastAPI service, a local Ollama model, technical and fundamental analysis, and an ML prediction lab behind one CLI, one API, and one web dashboard. The near term goal is trust: automated tests, repeatable releases, clear security defaults, and operations that a small team can run without guesswork. New analysis pages matter less than making the existing surface reliable and easy to deploy.

## Current state

OOBIR already works as a broad product. The FastAPI app serves data, AI analysis, trading strategy, ML prediction, batch export, screener, cache, and health routes. The CLI in `flow.py`, the static dashboard in `web/`, the ML package in `ml/`, the SQLite cache, the TimescaleDB schema, the daily sync scripts, and the Docker Compose stack with app, web, Ollama, Postgres, and sync containers are all present and documented. A Zenodo DOI and `CITATION.cff` were added in PR #71, and an ESLint advisory was fixed in PR #65.

Test status is strong but not enforced on main. PR #72 reports 420 tests passing with `pytest tests --ignore=tests/ui --ignore=tests/scripts`, and the README reports 76% coverage. The only workflow on main today is the manual Selenium smoke job in `.github/workflows/ui-selenium.yml`; there is no unit test job on push or pull request until PR #72 merges. The latest run for PR #72 passed. PR #73 keeps Selenium manual and restricts its permissions, and PR #74 marks `web/` assets as vendored. Dependabot is configured for pip, npm, Docker, and Actions, and recent update runs pass.

There are no open issues. Open pull requests are #66 through #70 for dependency updates, plus #72, #73, and #74 for the CI and repository hygiene work above. No `ROADMAP.md` existed before this file.

## Now (next 2 to 4 weeks)

- Review and merge PR #72 so every push and pull request runs the unit test suite; today a broken test can reach main. (S)
- Merge PR #73 so the Selenium smoke job stays manual, runs with read only permissions, and cancels stale runs. (S)
- Merge PR #74 so GitHub treats the static dashboard as vendored and reports Python as the main language. (S)
- Land Dependabot PRs #66 through #70 after a full test run so the declared minimum versions stay current. (S)
- Add a coverage report and a minimum threshold to the new test job; 76% is documented but nothing stops a regression. (M)
- Add a dependency audit and a static analysis security scan to CI so known advisories fail a build. (M)
- Write a short operations guide for env vars, API keys, ports, cache paths, and the daily sync container; this knowledge is split across README and compose. (S)
- Align the Python version across Docker, CI, and the README; Docker uses 3.15 while the new test job uses 3.11. (S)

## Next (1 to 3 months)

- Publish the app image to GHCR on tagged releases with a pinned digest and a matching compose example. (M)
- Add a release workflow that tags a version, writes a changelog, creates a GitHub release, and triggers the Zenodo archive; DOI metadata from PR #71 is still filled by hand. (M)
- Raise coverage to 85%, starting with `flow_api.py` at 67% and the data and AI routes. (L)
- Add integration tests that run against Postgres and TimescaleDB plus the daily sync scripts, which are mocked or skipped today. (M)
- Split `flow_api.py` into routers by domain to reduce the 86 KB module and make tests and ownership easier. (L)
- Run mypy, Black, Ruff, and ESLint in CI; the README documents these checks but no workflow enforces them. (M)
- Remove the default development API key from the image and add key rotation or hashed keys; the Dockerfile still ships a known value. (M)
- Make CORS origins configurable through env vars instead of a broad list of local and LAN origins. (S)
- Add request and dependency metrics plus a database health check so `/health/deps` covers Postgres and cache state, not only the LLM. (M)
- Add a fallback data provider or clearer failure handling around yfinance outages and throttling. (M)

## Later

- Provide a Kubernetes or Helm deployment path with health probes and resource limits; compose is the only supported path today. (L)
- Add a model registry and scheduled retraining for `ml/` so predictors are reproducible and versioned. (L)
- Persist portfolio and watchlist data on the server with accounts, since both live only in browser storage today. (L)
- Add a provider interface for new market data sources and LLM backends so the core is not tied to one vendor. (L)
- Publish an API versioning and deprecation policy before external consumers depend on route shapes. (M)
- Add performance tests for the batch export and screener routes, which are the heaviest read paths. (M)

## Quality and DevOps

- Tests: keep 420 tests passing, add a coverage floor, and keep browser tests manual as agreed in PR #73. (M)
- CI: make pytest, lint, type check, and security scan required checks; the unit job arrives with PR #72. (M)
- Security: Dependabot is active, but add a dependency audit, static analysis, secret scan, and container scan. (M)
- Containers: move to multistage builds, an unprivileged user, a pinned base image, and published images. (M)
- Releases: add version tags, a changelog, GitHub releases, and one Zenodo DOI per version; PR #71 added the first DOI. (M)
- Observability: structured logs already exist, so add metrics, dashboards, and alert guidance. (M)

## Known risks

- yfinance is an unofficial data source that can change or throttle, and compose pins Yahoo IPs in `extra_hosts`, which can go stale. (High)
- The default API key in `Dockerfile` and compose can reach a public host unchanged. (High)
- Python and dependency drift is real: Docker uses 3.15, CI uses 3.11, and minimums for numpy, pandas, and FastAPI are recent, so a fresh install may fail. (Medium)
- Browser coverage is thin in CI and `web/app.js` is large, so UI regressions depend on manual Selenium runs. (Medium)
- Model artifacts in `models/` are ignored by git and were only just created on save in PR #72, so predictions are not reproducible across environments. (Medium)
- A single maintainer plus weekly Dependabot pull requests creates review load and stale branches. (Medium)
- LLM features need a large local Ollama model, which raises resource needs and makes demos slow. (Medium)
