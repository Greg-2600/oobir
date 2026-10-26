const API = window.location.origin;
console.log('=== SECTORS.JS LOADED ===');
console.log('API:', API);

const SECTORS = [
    { ticker: 'XLF',  name: 'Financials',      color: '#3b82f6', description: 'Banks, insurance, asset management', longName: 'Financial Select Sector SPDR Fund' },
    { ticker: 'XLK',  name: 'Technology',       color: '#8b5cf6', description: 'Software, hardware, semiconductors', longName: 'Technology Select Sector SPDR Fund' },
    { ticker: 'XLE',  name: 'Energy',           color: '#f59e0b', description: 'Oil, gas, renewables', longName: 'Energy Select Sector SPDR Fund' },
    { ticker: 'XLV',  name: 'Healthcare',       color: '#10b981', description: 'Pharma, biotech, medical devices', longName: 'Health Care Select Sector SPDR Fund' },
    { ticker: 'XLY',  name: 'Consumer Disc.',   color: '#ec4899', description: 'Retail, autos, hospitality', longName: 'Consumer Discretionary Select Sector SPDR Fund' },
    { ticker: 'XLP',  name: 'Consumer Staples', color: '#14b8a6', description: 'Food, household, staples', longName: 'Consumer Staples Select Sector SPDR Fund' },
    { ticker: 'XLI',  name: 'Industrials',      color: '#f97316', description: 'Aerospace, defense, construction', longName: 'Industrial Select Sector SPDR Fund' },
    { ticker: 'XLB',  name: 'Materials',        color: '#a78bfa', description: 'Chemicals, mining, materials', longName: 'Materials Select Sector SPDR Fund' },
    { ticker: 'XLRE', name: 'Real Estate',      color: '#fb923c', description: 'REITs, real estate holding', longName: 'Real Estate Select Sector SPDR Fund' },
    { ticker: 'XLC',  name: 'Comm. Services',   color: '#06b6d4', description: 'Telecom, media, entertainment', longName: 'Communication Services Select Sector SPDR Fund' },
    { ticker: 'XLU',  name: 'Utilities',        color: '#84cc16', description: 'Electric, water, gas utilities', longName: 'Utilities Select Sector SPDR Fund' },
];

const GROWTH = ['XLK', 'XLY', 'XLC', 'XLRE'];
const DEFENSIVE = ['XLP', 'XLU', 'XLV', 'XLB'];

let sectorData = {};

async function fetchSectorData(ticker, days = 30) {
    try {
        const [priceRes, fundRes] = await Promise.all([
            fetch(`${API}/api/price-history/${ticker}?days=${days}`),
            fetch(`${API}/api/fundamentals/${ticker}`).catch(() => null)
        ]);
        let priceJson = priceRes.ok ? await priceRes.json() : null;
        const priceData = priceJson && priceJson.data ? priceJson.data : (priceJson || null);
        const fundData = fundRes && fundRes.ok ? await fundRes.json() : null;
        return { priceData, fundData };
    } catch (_e) {
        return { priceData: null, fundData: null };
    }
}

function calcChange(prices) {
    if (!prices || prices.length < 2) return null;
    const first = prices[0].Close;
    const last = prices[prices.length - 1].Close;
    return ((last - first) / first) * 100;
}

function calcChangesMulti(prices, windows = [5, 20, 60, 180]) {
    if (!prices || prices.length < 2) return {};
    const result = {};
    for (const w of windows) {
        if (prices.length > w) {
            const old = prices[prices.length - 1 - w].Close;
            const cur = prices[prices.length - 1].Close;
            result[w] = ((cur - old) / old) * 100;
        }
    }
    return result;
}

async function loadAllSectors() {
    loadMacroStats();
    await Promise.all(SECTORS.map(s => loadSector(s)));
    updateMacroStats();
    renderRotationRankings();
    renderHeatmap();
}

async function loadSector(sector) {
    const { priceData, fundData } = await fetchSectorData(sector.ticker);
    if (!priceData || !priceData.length || priceData.length < 5) return;

    const prices = priceData;
    const changes = calcChangesMulti(prices);
    const change1m = changes[20] ?? calcChange(prices.slice(-22));
    const change1w = changes[5] ?? null;
    const change3m = changes[60] ?? null;
    const latestPrice = prices[prices.length - 1].Close;

    sectorData[sector.ticker] = { prices, changes, change1m, change1w, change3m, latestPrice, fundData };
}

async function loadMacroStats() {
    try {
        const res = await fetch(`${API}/api/price-history/SPY?days=30`);
        if (res.ok) {
            const raw = await res.json();
            const d = raw.data ? raw.data : raw;
            if (d && d.length > 1) {
                const spy = calcChange(d);
                const sign = spy >= 0 ? '+' : '';
                const el = document.getElementById('macro-spy');
                if (el) {
                    el.textContent = sign + spy.toFixed(2) + '%';
                    el.className = 'macro-stat-value ' + (spy > 0 ? 'up' : spy < 0 ? 'down' : '');
                }
                const subEl = document.getElementById('macro-spy-change');
                if (subEl) subEl.textContent = 'SPY 1-month change';
            }
        }
    } catch (e) { console.error(e); }
}

function updateMacroStats() {
    const data = Object.entries(sectorData);
    if (!data.length) return;

    const changes = data.map(([, d]) => d.change1m).filter(v => v !== null);
    const avg = changes.reduce((a, b) => a + b, 0) / changes.length;
    const sign = avg >= 0 ? '+' : '';
    const avgEl = document.getElementById('macro-avg-mom');
    if (avgEl) {
        avgEl.textContent = sign + avg.toFixed(2) + '%';
        avgEl.className = 'macro-stat-value ' + (avg > 0 ? 'up' : 'down');
    }

    const sorted = [...changes].sort((a, b) => b - a);
    const spread = (sorted[0] || 0) - (sorted[sorted.length - 1] || 0);
    const leadEl = document.getElementById('macro-lead');
    if (leadEl) {
        leadEl.textContent = spread.toFixed(1) + 'pp';
    }
    const leadSubEl = document.getElementById('macro-lead-sub');
    if (leadSubEl && sorted.length) {
        leadSubEl.textContent = `${sorted[0].toFixed(1)}% top vs ${sorted[sorted.length - 1].toFixed(1)}% bottom`;
    }

    const growthAvgs = data.filter(([t]) => GROWTH.includes(t)).map(([, d]) => d.change1m);
    const defAvgs = data.filter(([t]) => DEFENSIVE.includes(t)).map(([, d]) => d.change1m);
    const growthAvg = growthAvgs.length ? growthAvgs.reduce((a, b) => a + b) / growthAvgs.length : 0;
    const defAvg = defAvgs.length ? defAvgs.reduce((a, b) => a + b) / defAvgs.length : 0;
    const riskSpread = growthAvg - defAvg;
    const riskEl = document.getElementById('macro-risk');
    if (riskEl) {
        riskEl.textContent = (riskSpread >= 0 ? '+' : '') + riskSpread.toFixed(1) + 'pp';
    }
    const riskSubEl = document.getElementById('macro-risk-sub');
    if (riskSubEl) {
        riskSubEl.textContent = riskSpread > 2 ? 'Risk-on atmosphere' : riskSpread < -2 ? 'Risk-off rotation' : 'Neutral';
    }

    let aboveSMA = 0;
    for (const [, d] of data) {
        if (!d.prices || d.prices.length < 22) continue;
        const cur = d.prices[d.prices.length - 1].Close;
        const sma20 = d.prices.slice(-22).reduce((s, p) => s + p.Close, 0) / Math.min(22, d.prices.length);
        if (cur > sma20) aboveSMA++;
    }
    const breadthEl = document.getElementById('macro-breadth');
    if (breadthEl) {
        breadthEl.textContent = `${aboveSMA}/${data.length}`;
        breadthEl.className = 'macro-stat-value ' + (aboveSMA > data.length / 2 ? 'up' : 'down');
    }
}

function renderRotationRankings() {
    const entries = Object.entries(sectorData)
        .map(([ticker, d]) => ({ ticker, ...d }))
        .filter(d => d.change1m !== null)
        .sort((a, b) => b.change1m - a.change1m);

    const container = document.getElementById('rotation-rankings');
    if (!entries.length) return;

    container.innerHTML = entries.map((e, i) => {
        const sector = SECTORS.find(s => s.ticker === e.ticker);
        const sign1m = e.change1m >= 0 ? '+' : '';
        const sign1w = e.change1w !== null ? (e.change1w >= 0 ? '+' : '') : '';
        const sign3m = e.change3m !== null ? (e.change3m >= 0 ? '+' : '') : '';
        const rankClass = i === 0 ? 'rank-1' : i === entries.length - 1 ? 'rank-last' : '';

        let barsHtml = '';
        if (e.prices && e.prices.length > 5) {
            const bars = e.prices.slice(-20);
            const min = Math.min(...bars.map(b => b.Low));
            const max = Math.max(...bars.map(b => b.High));
            const range = max - min || 1;
            const color = e.change1m > 0 ? '#10b981' : e.change1m < 0 ? '#ef4444' : '#6b7280';
            barsHtml = bars.map(b => {
                const h = Math.max(3, ((b.Close - min) / range) * 40);
                return `<div style="flex:1; height:${h}px; background:${color}; opacity:0.7; border-radius:1px 1px 0 0;"></div>`;
            }).join('');
        }

        return `
            <div class="rotation-item ${rankClass}" onclick="openSectorDetail('${e.ticker}')" style="cursor:pointer;">
                <div class="rotation-rank">#${i + 1}</div>
                <div class="rotation-info">
                    <div class="rotation-ticker">${sector ? sector.name : e.ticker}</div>
                    <div style="font-size:0.7rem; color:#64748b;">${e.ticker} · $${e.latestPrice ? e.latestPrice.toFixed(2) : '—'}</div>
                    ${barsHtml ? `<div style="display:flex; gap:1px; height:44px; margin-top:6px;">${barsHtml}</div>` : ''}
                </div>
                <div class="rotation-metrics">
                    <div class="rotation-metric"><span class="rotation-metric-label">1W</span><span style="color:${e.change1w !== null && e.change1w >= 0 ? '#10b981' : '#ef4444'}">${e.change1w !== null ? sign1w + e.change1w.toFixed(1) + '%' : '—'}</span></div>
                    <div class="rotation-metric"><span class="rotation-metric-label">1M</span><span style="color:${e.change1m >= 0 ? '#10b981' : '#ef4444'}; font-weight:700;">${sign1m}${e.change1m.toFixed(1)}%</span></div>
                    <div class="rotation-metric"><span class="rotation-metric-label">3M</span><span style="color:${e.change3m !== null && e.change3m >= 0 ? '#10b981' : '#ef4444'}">${e.change3m !== null ? sign3m + e.change3m.toFixed(1) + '%' : '—'}</span></div>
                </div>
            </div>
        `;
    }).join('');
}

function renderHeatmap() {
    const container = document.getElementById('heatmap-grid');
    const entries = Object.entries(sectorData)
        .filter(([, d]) => d.change1m !== null)
        .sort((a, b) => b[1].change1m - a[1].change1m);

    if (!entries.length) {
        container.innerHTML = '<div class="loading-state">No data available</div>';
        return;
    }

    const maxAbs = Math.max(...entries.map(([, d]) => Math.abs(d.change1m)));

    container.innerHTML = entries.map(([ticker, d]) => {
        const sector = SECTORS.find(s => s.ticker === ticker);
        const intensity = Math.abs(d.change1m) / maxAbs;
        const bg = d.change1m > 0
            ? `rgba(16, 185, 129, ${0.15 + intensity * 0.7})`
            : `rgba(239, 68, 68, ${0.15 + intensity * 0.7})`;
        const sign = d.change1m >= 0 ? '+' : '';
        return `
            <div class="heatmap-cell" style="background:${bg};">
                <div style="font-weight:700; font-size:0.85rem;">${ticker}</div>
                <div style="font-size:0.75rem;">${sign}${d.change1m.toFixed(1)}%</div>
                <div style="font-size:0.65rem; opacity:0.8;">${sector ? sector.name.split(' ')[0] : ''}</div>
            </div>
        `;
    }).join('');
}

function initTheme() {
    const saved = localStorage.getItem('oobir_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
}
document.getElementById('theme-toggle').addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('oobir_theme', next);
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.textContent = next === 'dark' ? '☀️' : '🌙';
});

function openSectorDetail(ticker) { // eslint-disable-line no-unused-vars
    const d = sectorData[ticker];
    const sector = SECTORS.find(s => s.ticker === ticker);
    if (!d || !sector) return;

    document.getElementById('detail-sector-name').textContent = sector.longName;
    document.getElementById('detail-sector-desc').textContent = sector.description;
    document.getElementById('detail-sector-price').textContent = '$' + d.latestPrice.toFixed(2);

    const change1wEl = document.getElementById('detail-1w');
    const change1mEl = document.getElementById('detail-1m');
    const change3mEl = document.getElementById('detail-3m');
    const ytdEl = document.getElementById('detail-ytd');

    if (change1wEl) change1wEl.textContent = d.change1w !== null ? (d.change1w >= 0 ? '+' : '') + d.change1w.toFixed(2) + '%' : '—';
    if (change1mEl) change1mEl.textContent = d.change1m !== null ? (d.change1m >= 0 ? '+' : '') + d.change1m.toFixed(2) + '%' : '—';
    if (change3mEl) change3mEl.textContent = d.change3m !== null ? (d.change3m >= 0 ? '+' : '') + d.change3m.toFixed(2) + '%' : '—';
    if (ytdEl) ytdEl.textContent = d.change3m !== null ? (d.change3m >= 0 ? '+' : '') + d.change3m.toFixed(2) + '%' : '—';

    const chartEl = document.getElementById('detail-chart');
    if (chartEl && d.prices && d.prices.length) {
        const bars = d.prices.slice(-60);
        const min = Math.min(...bars.map(b => b.Low));
        const max = Math.max(...bars.map(b => b.High));
        const range = max - min || 1;
        const color = d.change1m > 0 ? '#10b981' : d.change1m < 0 ? '#ef4444' : '#6b7280';
        chartEl.innerHTML = bars.map(b => {
            const h = Math.max(4, ((b.Close - min) / range) * 180);
            return `<div style="flex:1; height:${h}px; background:${color}; border-radius:2px 2px 0 0;"></div>`;
        }).join('');
    }

    const holdingsEl = document.getElementById('detail-holdings');
    if (holdingsEl) {
        holdingsEl.innerHTML = '<div style="color:#94a3b8; font-size:0.85rem;">Holdings data not available</div>';
    }

    document.getElementById('sector-detail').style.display = 'block';
}

function closeSectorDetail() { // eslint-disable-line no-unused-vars
    document.getElementById('sector-detail').style.display = 'none';
}

initTheme();
loadAllSectors();
