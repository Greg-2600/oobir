# Market Briefing Dashboard

> **Live page:** [`web/dashboard.html`](../../web/dashboard.html) — served at `/dashboard.html`
>
> A single-page, self-refreshing overview of the day's market. Everything worth
> knowing at a glance, on one screen, updated every hour.

![Market Briefing dashboard](../screenshots/07_market_briefing.png)

---

## 1. Why it exists

OOBIR already had a dozen deep-dive pages — correlation matrices, backtesters,
option chains, earnings calendars. Each one is excellent for a single question,
but answering "what is the market doing today?" meant opening four or five
tabs.

The Market Briefing collapses that into one screen:

- **One viewport.** The page pins to `100vh` with no page-level scrolling.
- **Self-updating.** Rebuilds itself every 60 minutes; no reload required.
- **Honest about loading.** Every card shows its own progress indicator, so a
  slow endpoint never looks like an empty card.
- **Readable.** Every ticker is shown with its full company name, and hovering
  reveals sector and industry detail.

---

## 2. Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ SPY        QQQ        DIA        IWM          ← index snapshot        │
│ name       name       name       name                                │
├────────────────────────────────┬─────────────────────────────────────┤
│ FUTURES                       │ SENTIMENT                            │
│ S&P 500 / NASDAQ / RUSSELL …  │  62  Greed   VIX · P/C · A/D        │
├────────────────────────────────┼─────────────────────────────────────┤
│ TOP MOVERS                    │ ML DIRECTION (5d)   │ EARNINGS       │
│ ticker · company · price · …  │ confidence bars     │ BMO/AMC · EPS  │
├────────────────────────────────┼─────────────────────┴───────────────┤
│ KEY MACRO EVENTS              │ SECTOR ROTATION — PERFORMANCE       │
│ TODAY · TMRW · OCT 30 …       │ leaders (left) · laggards (right)    │
└────────────────────────────────┴─────────────────────────────────────┘
```

The grid is CSS-only and reflows with the viewport. Rows share height via
`grid-template-columns` ratios, and every card body is a flex column with
`overflow: auto`, so a card with more rows than space scrolls internally
instead of clipping.

---

## 3. The nine cards

| Card | Source | Notes |
|---|---|---|
| **Index snapshot** | `/api/price-history/{symbol}?days=2` | SPY, QQQ, DIA, IWM — price and % change vs. prior close |
| **Futures & pre-market** | static | ES, NQ, RTY, CL, GC, DXY with instrument descriptions |
| **Sentiment** | derived from SPY history | Fear & Greed gauge, VIX proxy, put/call ratio, A/D breadth |
| **Top movers** | `/api/price-history/{symbol}?days=2` | 15 tickers ranked by absolute % move; `GAP` badge past 5% |
| **ML direction (5d)** | `/api/predict/{symbol}?horizon=5` | Model direction and up-probability per ticker |
| **Earnings this week** | curated list | BMO/AMC badge, date and EPS estimate |
| **Key macro events** | curated list | ISM, Retail Sales, NFP, CPI, FOMC with impact rating |
| **Sector rotation** | static | 10 SPDR sectors × 3M/6M/YTD/1Y, colour-coded heatmap |

---

## 4. Company names

Ticker codes alone are hard to scan, so every ticker is paired with its full
company name.

Names are resolved in two steps to keep it to a single network round trip:

```js
// 1. One bulk call covers ~500 tickers
await api('/api/fundamentals-db?limit=500');

// 2. Fall back to per-symbol for anything missing (e.g. small caps)
await loadMissingNames(MOVERS_TICKERS.concat(ML_TICKERS).concat(EARNINGS_TICKERS));
```

The bulk endpoint returns `long_name` alongside `ticker`, `sector`, `industry`
and `exchange`. `loadMissingNames()` fills the gaps from
`/api/fundamentals/{symbol}`, which returns `longName` from the data provider.

The four index ETFs are not equities, so they carry static fund names:

| Ticker | Name |
|---|---|
| SPY | SPDR S&P 500 ETF Trust |
| QQQ | Invesco QQQ Trust (Nasdaq 100) |
| DIA | SPDR Dow Jones Industrial Average ETF |
| IWM | iShares Russell 2000 ETF |

---

## 5. Tooltips

A single floating tooltip element (`#oobir-tip`) follows the cursor and is
driven by data attributes, so any element can opt in:

```html
<span data-tip="NVIDIA Corporation"
      data-tip-title="NVIDIA Corporation"
      data-tip-sub="Technology · Semiconductors">NVDA</span>
```

`positionTip()` clamps the tooltip inside the viewport and flips it below the
cursor when there is no room above.

| Hover target | Tooltip shows |
|---|---|
| Any ticker | Full company name, sector, industry |
| Futures card | Instrument name and what it tracks |
| Macro event | Event name and what it measures |
| Sector row | Sector name and what it contains |
| Earnings row | Company name plus the reporting date |

---

## 6. Loading states

Every card starts in a loading state and swaps to content when its own
request settles:

```html
<div id="ml-signals" data-loading="true">
  <div class="loading-wrap"><div class="loading-dots">LOADING</div></div>
</div>
```

`refreshAll()` marks **all** sections as loading up front, then fans out the
requests:

```js
setLoading($('futures-row'));
setLoading($('ml-signals'));
// ...
loadFutures();   // no API needed — render immediately
loadEarnings();  // no API needed — render immediately
await Promise.all([
    loadIndices(), loadSentiment(), loadMovers(),
    loadMlSignals(), loadMacroEvents(), loadSectorRotation(),
]);
```

Futures and earnings need no network call, so they render *before* the
`await`. Otherwise they would sit blank for the several seconds it takes the
slowest price-history request to resolve.

Each loader also re-arms its own loading state when it starts, so a manual
refresh shows progress in every card rather than leaving stale data on screen.

---

## 7. Refresh behaviour

```js
refreshAll();
setInterval(refreshAll, 60 * 60 * 1000);  // hourly
```

The `↻ Refresh` button in the top bar calls `refreshAll()` directly. The
timestamp next to it shows when the last successful refresh completed.

---

## 8. API base URL

The dashboard resolves the API from the serving origin:

```js
const API = window.location.origin;
```

There is no hardcoded host. The page works unchanged on `localhost`, behind
the nginx reverse proxy, or on any other host — requests go to
`/api/...` on whatever origin served the page.

---

## 9. Caching headers

`web/nginx.conf` marks live dashboards as uncacheable so browsers never serve
a stale copy of the HTML:

```nginx
location ~* ^/(dashboard|news-timeline|predictions|portfolio|watchlist|money-flow|options)\.html$ {
    add_header Cache-Control "no-store, no-cache, must-revalidate, max-age=0" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;
    try_files $uri $uri/ =404;
}
```

---

## 10. Testing

`tests/test_dashboard_ui.py` holds 31 static contract tests — no browser or
network required.

| Group | Covers |
|---|---|
| `TestDashboardPageContracts` | Section ids exist, ids are unique, relative API base, nav links |
| `TestDashboardLoadingStates` | Loading styles exist, sections start in loading state, loading is set before awaiting |
| `TestDashboardCompanyNames` | Bulk name load, per-symbol fallback, static ETF names, name rendering |
| `TestDashboardTooltips` | Tooltip element, data attributes, viewport clamping |
| `TestDashboardRefreshBehaviour` | Hourly interval, instant sections render before the await, manual refresh, theme toggle |
| `TestDashboardScriptValidity` | No duplicate declarations in the same scope, balanced braces, helpers defined |
| `TestDashboardApiContract` | Every endpoint the page calls exists in `flow_api.py` |

### The duplicate-declaration guard

A single duplicated `const` inside one function is a **SyntaxError**. The
browser then discards the *entire* inline script block — the page freezes on
its loading state forever, with nothing visible in the console to explain why.

That failure mode is silent and expensive to debug, so it is guarded by a
test. The scanner walks the script tracking brace scope, so two functions may
each declare their own `const rows` without being flagged, while two
`const score` in the *same* function are:

```python
def test_no_duplicate_declarations_in_same_scope(self):
    script = "\n".join(_inline_scripts(DASHBOARD.read_text(encoding="utf-8")))

    seen = {}
    duplicates = []
    for scope, kind, name in _scoped_declarations(script):
        key = (scope, name)
        if key in seen:
            duplicates.append(f"{name} (declared twice in the same scope)")
        else:
            seen[key] = kind

    self.assertEqual(duplicates, [], f"Duplicate declarations: {duplicates}")
```

Run them with:

```bash
pytest tests/test_dashboard_ui.py -v
```

---

## 11. Limitations

- **Futures, earnings and macro events are curated static data.** There is no
  live futures feed or economic-calendar API wired in yet; the values are
  placeholders that need a real feed to become useful.
- **The sentiment score is illustrative.** VIX is derived from SPY's realised
  volatility as a proxy; the Fear & Greed value itself is a placeholder.
- **Sector rotation is static.** The heatmap reflects hardcoded performance
  rather than live sector ETF quotes.
- **Earnings dates are curated.** A live earnings feed would replace the
  static list.
