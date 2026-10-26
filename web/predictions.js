/*jslint browser*/

(function () {
    'use strict';

    const API = (typeof window !== 'undefined' && window.OOBIR_API_BASE)
        ? window.OOBIR_API_BASE
        : window.location.origin;

    let currentTicker = null;
    let priceData = null;
    let prediction = null;
    let abortController = null;

    const $ = (id) => document.getElementById(id);

    function el(id) { return $(id); }
    function setText(id, text) { const n = el(id); if (n) n.textContent = text; }
    function setHtml(id, html) { const n = el(id); if (n) n.innerHTML = html; }
    function setStyle(id, prop, val) { const n = el(id); if (n) n.style[prop] = val; }

    function showError(message) {
        setHtml('ml-error-slot',
            '<div class="ml-error">⚠️ ' + escapeHtml(message) + '</div>');
    }
    function clearError() { setHtml('ml-error-slot', ''); }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = String(text === null || text === undefined ? '' : text);
        return div.innerHTML;
    }

    function normalizeTicker(value) {
        return String(value || '').trim().toUpperCase();
    }

    function confidenceClass(conf) {
        return 'conf-' + String(conf || 'LOW');
    }

    // ── Fetch helpers ────────────────────────────────────────────────────────

    function newSession() {
        if (abortController) abortController.abort();
        abortController = new AbortController();
        return abortController.signal;
    }

    async function fetchJson(path, signal) {
        const controller = signal || (abortController ? abortController.signal : null);
        const opts = controller ? { signal: controller } : {};
        const resp = await fetch(API + path, opts);
        if (!resp.ok) {
            let detail = 'HTTP ' + resp.status;
            try {
                const body = await resp.json();
                if (body && body.detail) detail = body.detail;
            } catch {
                /* non-JSON error body; keep the HTTP status detail */
            }
            const err = new Error(detail);
            err.status = resp.status;
            throw err;
        }
        return resp.json();
    }

    // ── Model Lab state ───────────────────────────────────────────────────────

    let mlOptions = null;          // {models, feature_groups, defaults, bounds}
    let selectedGroups = [];       // active feature group names

    async function loadOptions() {
        try {
            mlOptions = await fetchJson('/api/ml/options');
            buildModelSelect();
            buildFeatureChips();
            applyKnobs(mlOptions.defaults);
        } catch (err) {
            setLabStatus('Could not load model options: ' + (err.message || err));
        }
    }

    function buildModelSelect() {
        const select = el('lab-model');
        if (!select || !mlOptions) return;
        select.innerHTML = mlOptions.models.map(m =>
            '<option value="' + escapeHtml(m.name) + '">' + escapeHtml(m.label) + '</option>'
        ).join('');
        select.addEventListener('change', updateModelDesc);
        updateModelDesc();
    }

    function updateModelDesc() {
        if (!mlOptions) return;
        const name = el('lab-model').value;
        const model = mlOptions.models.find(m => m.name === name);
        setText('lab-model-val', model ? model.label : name);
        setText('lab-model-desc', model ? model.description : '');
    }

    function buildFeatureChips() {
        const wrap = el('lab-feature-chips');
        if (!wrap || !mlOptions) return;
        selectedGroups = mlOptions.feature_groups.map(g => g.name);
        wrap.innerHTML = mlOptions.feature_groups.map(g =>
            '<button type="button" class="chip active" data-group="' + escapeHtml(g.name) + '" ' +
            'title="' + escapeHtml(g.columns.join(', ')) + '">' +
            escapeHtml(g.name) + ' · ' + g.count + '</button>'
        ).join('');
        wrap.querySelectorAll('.chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const name = chip.getAttribute('data-group');
                if (selectedGroups.includes(name)) {
                    selectedGroups = selectedGroups.filter(g => g !== name);
                    chip.classList.remove('active');
                } else {
                    selectedGroups.push(name);
                    chip.classList.add('active');
                }
                if (!selectedGroups.length) {
                    // Never allow an empty feature set; re-add all.
                    selectedGroups = mlOptions.feature_groups.map(g => g.name);
                    wrap.querySelectorAll('.chip').forEach(c => c.classList.add('active'));
                }
                updateFeaturesLabel();
            });
        });
        updateFeaturesLabel();
    }

    function updateFeaturesLabel() {
        setText('lab-features-val',
            selectedGroups.length === mlOptions.feature_groups.length
                ? 'all' : selectedGroups.length + ' groups');
    }

    function applyKnobs(knobs) {
        if (!knobs) return;
        if (knobs.model_name) el('lab-model').value = knobs.model_name;
        el('lab-horizon').value = knobs.horizon;
        el('lab-margin').value = Math.round((knobs.margin || 0) * 1000);
        el('lab-folds').value = knobs.folds;
        el('lab-max-train').value = knobs.max_train;
        if (Array.isArray(knobs.feature_groups)) {
            selectedGroups = knobs.feature_groups.slice();
            const wrap = el('lab-feature-chips');
            if (wrap) {
                wrap.querySelectorAll('.chip').forEach(chip => {
                    const name = chip.getAttribute('data-group');
                    chip.classList.toggle('active', selectedGroups.includes(name));
                });
            }
            updateFeaturesLabel();
        }
        updateModelDesc();
        syncKnobLabels();
    }

    function readKnobs() {
        return {
            model_name: el('lab-model').value || 'hist_gbm',
            horizon: parseInt(el('lab-horizon').value, 10) || 5,
            margin: (parseInt(el('lab-margin').value, 10) || 0) / 1000,
            feature_groups: selectedGroups.slice(),
            folds: parseInt(el('lab-folds').value, 10) || 3,
            max_train: parseInt(el('lab-max-train').value, 10) || 200,
        };
    }

    function syncKnobLabels() {
        const k = readKnobs();
        setText('lab-horizon-val', k.horizon + 'd');
        setText('lab-margin-val', (k.margin * 100).toFixed(1) + '%');
        setText('lab-folds-val', String(k.folds));
        setText('lab-train-val', String(k.max_train));
        updateModelDesc();
        updateFeaturesLabel();
    }

    function setLabStatus(message) { setText('lab-status', message); }

    function setPanelLoading(id, message) {
        setHtml(id, '<div class="ml-loading"><span class="ml-spinner"></span> ' + escapeHtml(message) + '</div>');
    }

    // ── Run the experiment ────────────────────────────────────────────────────

    async function run() {
        // Get ticker from stock page context, or fall back to input field
        let ticker = normalizeTicker(window.currentTicker || '');
        if (!ticker) {
            const symEl = document.getElementById('stock-symbol');
            if (symEl) ticker = normalizeTicker(symEl.textContent || '');
        }
        if (!ticker) {
            ticker = normalizeTicker(el('ml-ticker-input') ? el('ml-ticker-input').value : '');
        }
        if (!ticker) { showError('No ticker available. Search for a stock first.'); return; }
        const signal = newSession();
        currentTicker = ticker;
        clearError();
        setLoading();
        showRunningOverlay('⚡ Running experiment…', 'Training model & computing predictions — this takes a few seconds');
        setPanelLoading('ml-features', 'Fitting model & computing drivers…');
        setPanelLoading('ml-backtest', 'Running walk-forward backtest…');
        setLabStatus('Running experiment…');

        // Pulse the header to draw attention
        const header = el('ml-prediction-card');
        if (header) header.classList.add('ml-lab-pulse');
        const runBtn = el('ml-lab-run');
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.style.opacity = '0.7';
            runBtn.style.cursor = 'not-allowed';
        }

        const knobs = readKnobs();
        const query = [
            'model_name=' + encodeURIComponent(knobs.model_name),
            'horizon=' + knobs.horizon,
            'margin=' + knobs.margin,
            'feature_groups=' + encodeURIComponent(knobs.feature_groups.join(',')),
            'folds=' + knobs.folds,
            'max_train=' + knobs.max_train,
        ].join('&');

        try {
            priceData = await loadPriceAndChart(ticker, signal);
            const result = await fetchJson(
                '/api/predict/' + encodeURIComponent(ticker) + '/explore?' + query,
                signal
            );
            prediction = result;
            if (el('ml-results')) el('ml-results').style.display = 'grid';
            renderPrediction(result);
            renderRunBadges(result);
            renderMeta();
            renderChart();
            renderCompare();
            renderFeatures(result.features || []);
            renderBacktest(result.backtest || {});
            renderBalance(result.class_balance || {});
            setLabStatus('Trained on ' + (result.n_samples || 0) + ' rows · ' +
                (result.n_features || 0) + ' features');
        } catch (err) {
            if (err && err.name === 'AbortError') return;
            el('ml-results').style.display = 'none';
            setLabStatus('Experiment failed.');
            showError((err && err.message) || 'Unable to run prediction.');
        } finally {
            hideRunningOverlay();
            const header = el('ml-prediction-card');
            if (header) header.classList.remove('ml-lab-pulse');
            const runBtn = el('ml-lab-run');
            if (runBtn) {
                runBtn.disabled = false;
                runBtn.style.opacity = '';
                runBtn.style.cursor = '';
            }
        }
    }

    function renderRunBadges(r) {
        const wrap = el('ml-run-badges');
        if (!wrap) return;
        const model = (mlOptions && mlOptions.models.find(m => m.name === r.model_name));
        const badges = [
            '🧠 ' + (model ? model.label : r.model_name || '—'),
            '⏱️ ' + r.horizon_days + 'd horizon',
            '±' + ((r.margin || 0) * 100).toFixed(1) + '% flat band',
            '🔢 ' + r.n_features + ' features',
            '🎲 ' + (r.backtest ? r.backtest.folds : '—') + ' folds',
        ];
        wrap.innerHTML = badges.map(b => '<span class="badge">' + escapeHtml(b) + '</span>').join('');
    }

    function renderBalance(balance) {
        const box = el('ml-balance');
        if (!box) return;
        const entries = Object.entries(balance || {});
        if (!entries.length) { setHtml('ml-balance', '<div class="ml-empty">No class balance available</div>'); return; }
        const total = entries.reduce((a, [, v]) => a + v, 0) || 1;
        const colors = { UP: '#10b981', DOWN: '#ef4444', FLAT: '#94a3b8' };
        setHtml('ml-balance',
            '<div class="class-balance">' + entries.map(([k, v]) =>
                '<span><b style="color:' + (colors[k] || '#1f2937') + ';">' +
                escapeHtml(k) + '</b> ' + v + ' (' + ((v / total) * 100).toFixed(1) + '%)</span>'
            ).join('') + '</div>' +
            '<div class="lab-model-desc" style="margin-top:8px;">Rows before the warm-up trim are excluded; this is the exact training set for the run above.</div>'
        );
    }

    function setLoading() {
        ['ml-direction', 'ml-meta'].forEach(id => setText(id, 'Loading…'));
        ['ml-bar-up', 'ml-bar-flat', 'ml-bar-down'].forEach(id => setStyle(id, 'width', '0%'));
        setStyle('ml-conf', 'background', '#f1f5f9');
        setText('ml-conf', '…');
    }

    function showRunningOverlay(title, sub) {
        const overlay = el('ml-lab-overlay');
        if (!overlay) return;
        const titleEl = el('ml-overlay-title');
        const subEl = el('ml-overlay-sub');
        if (titleEl) titleEl.textContent = title;
        if (subEl) subEl.textContent = sub;
        overlay.classList.remove('hidden');
    }

    function hideRunningOverlay() {
        const overlay = el('ml-lab-overlay');
        if (overlay) overlay.classList.add('hidden');
    }

    // ── Rendering ────────────────────────────────────────────────────────────

    function dirMeta(dir) {
        if (dir === 'UP') return { icon: '📈', color: '#10b981', words: 'Bullish bias' };
        if (dir === 'DOWN') return { icon: '📉', color: '#ef4444', words: 'Bearish bias' };
        return { icon: '↔️', color: '#64748b', words: 'Range-bound' };
    }

    function renderPrediction(p) {
        const meta = dirMeta(p.direction);
        setText('ml-icon', meta.icon);
        setText('ml-direction', p.direction);
        setStyle('ml-direction', 'color', meta.color);
        const model = (mlOptions && mlOptions.models.find(m => m.name === p.model_name));
        const modelLabel = model ? model.label : (p.model_name || 'model');
        setText('ml-meta',
            meta.words + ' · ' + modelLabel + ' · ' + p.horizon_days + 'd · v' + p.model_version);

        const up = p.prob_up || 0, flat = p.prob_flat || 0, down = p.prob_down || 0;
        setBar('ml-bar-up', up); setText('ml-pct-up', (up * 100).toFixed(1) + '%');
        setBar('ml-bar-flat', flat); setText('ml-pct-flat', (flat * 100).toFixed(1) + '%');
        setBar('ml-bar-down', down); setText('ml-pct-down', (down * 100).toFixed(1) + '%');

        const conf = el('ml-conf');
        conf.textContent = p.confidence;
        conf.className = 'conf-badge ' + confidenceClass(p.confidence);
    }

    function setBar(id, frac) {
        const bar = el(id);
        if (!bar) return;
        bar.style.width = Math.max(0, Math.min(1, (frac || 0))) * 100 + '%';
    }

    function renderMeta() {
        // Keep chart-empty overlay hidden once a forecast exists.
        const emptyEl = el('ml-chart-empty');
        if (emptyEl) emptyEl.style.display = 'none';
    }

    async function loadPriceAndChart(ticker, signal) {
        const resp = await fetchJson('/api/price-history/' + encodeURIComponent(ticker), signal);
        const data = Array.isArray(resp) ? resp : (resp.data || resp.prices || []);
        return data;
    }

    function renderFeatures(features) {
        const list = el('ml-features');
        if (!list || !features.length) { setHtml('ml-features', '<li class="ml-empty">No feature importances available</li>'); return; }
        const max = features[0].importance || 1;
        list.innerHTML = features.map((f, i) =>
            '<li class="feat-row">' +
            '<span class="feat-rank">#' + (i + 1) + '</span>' +
            '<span class="feat-name">' + escapeHtml(f.feature) + '</span>' +
            '<div class="feat-bar"><div style="width:' + ((f.importance / max) * 100) + '%"></div></div>' +
            '</li>'
        ).join('');
    }

    function metricBox(label, value, tone) {
        return '<div class="metric-box ' + (tone || '') + '">' +
            '<div class="m-value">' + value + '</div>' +
            '<div class="m-label">' + label + '</div></div>';
    }

    function renderBacktest(bt) {
        const box = el('ml-backtest');
        if (!box) return;
        if (!bt || !bt.n_samples) {
            setHtml('ml-backtest', '<div class="ml-empty">' + escapeHtml((bt && bt.error) || 'No samples') + '</div>');
            return;
        }
        const accTone = bt.accuracy >= bt.baseline_accuracy ? 'good' : 'warn';
        const f1s = Object.values(bt.f1 || {});
        const avgF1 = f1s.length ? f1s.reduce((a, b) => a + b, 0) / f1s.length : 0;
        setHtml('ml-backtest',
            metricBox('Accuracy', (bt.accuracy * 100).toFixed(1) + '%', accTone) +
            metricBox('Baseline', (bt.baseline_accuracy * 100).toFixed(1) + '%') +
            metricBox('Avg F1', avgF1.toFixed(2)) +
            metricBox('Samples', bt.n_samples) +
            metricBox('Horizon', bt.horizon_days + 'd') +
            metricBox('Majority', escapeHtml(bt.majority_class || '—'))
        );
    }

    function renderCompare() {
        const box = el('ml-compare');
        if (!box || !priceData) return;
        const closes = priceData.map(d => Number(d.Close)).filter(v => !isNaN(v));
        if (closes.length < 30) { setHtml('ml-compare', '<div class="ml-empty">Insufficient data for a heuristic comparison</div>'); return; }

        // Simple RSI(14) + MACD heuristic.
        const rsiVal = rsi(closes, 14);
        const macdVal = macd(closes);
        let bullish = 0, bearish = 0;
        if (rsiVal < 45) { bullish++; } else if (rsiVal > 55) { bearish++; }
        if (macdVal > 0) { bullish++; } else { bearish++; }

        let heur = 'NEUTRAL';
        if (bullish > bearish) heur = 'BULLISH';
        else if (bearish > bullish) heur = 'BEARISH';

        const mlDir = prediction ? prediction.direction : 'FLAT';
        const agree = (heur === 'BULLISH' && mlDir === 'UP') || (heur === 'BEARISH' && mlDir === 'DOWN') || (heur === 'NEUTRAL' && mlDir === 'FLAT');

        setHtml('ml-compare',
            '<div style="display:flex; gap:18px; flex-wrap:wrap; align-items:center;">' +
            '<div>' +
              '<div style="font-size:.78rem; color:#64748b; font-weight:700;">HEURISTIC RSI/MACD</div>' +
              '<div style="font-size:1.4rem; font-weight:900; color:' + (heur === 'BULLISH' ? '#10b981' : heur === 'BEARISH' ? '#ef4444' : '#64748b') + ';">' + heur + '</div>' +
              '<div style="font-size:.78rem; color:#64748b;">RSI ' + rsiVal.toFixed(1) + ' · MACD ' + (macdVal > 0 ? '+' : '') + macdVal.toFixed(2) + '</div>' +
            '</div>' +
            '<div style="font-size:2rem;color:#cbd5e1;">vs</div>' +
            '<div>' +
              '<div style="font-size:.78rem; color:#64748b; font-weight:700;">MACHINE LEARNING</div>' +
              '<div style="font-size:1.4rem; font-weight:900; color:' + (mlDir === 'UP' ? '#10b981' : mlDir === 'DOWN' ? '#ef4444' : '#64748b') + ';">' + mlDir + '</div>' +
              '<div style="font-size:.78rem; color:#64748b;">' + ((prediction && prediction.confidence) || '') + ' confidence</div>' +
            '</div>' +
            '<div style="margin-left:auto; text-align:center; background:' + (agree ? '#f0fdf4' : '#fef2f2') + '; color:' + (agree ? '#15803d' : '#b91c1c') + '; border-radius:999px; padding:8px 14px; font-weight:800; font-size:.85rem;">' +
              (agree ? '✓ Models agree' : '✗ Signals diverge') +
            '</div>' +
            '</div>'
        );
    }

    function rsi(closes, period) {
        if (closes.length < period + 1) return 50;
        let gain = 0, loss = 0;
        for (let i = 1; i <= period; i++) {
            const diff = closes[i] - closes[i - 1];
            if (diff >= 0) gain += diff; else loss -= diff;
        }
        let avgGain = gain / period, avgLoss = loss / period;
        for (let i = period + 1; i < closes.length; i++) {
            const diff = closes[i] - closes[i - 1];
            avgGain = (avgGain * (period - 1) + Math.max(diff, 0)) / period;
            avgLoss = (avgLoss * (period - 1) + Math.max(-diff, 0)) / period;
        }
        if (avgLoss === 0) return 100;
        const rs = avgGain / avgLoss;
        return 100 - (100 / (1 + rs));
    }

    function macd(closes) {
        if (closes.length < 26) return 0;
        const ema = (data, span) => {
            const k = 2 / (span + 1);
            const out = [data[0]];
            for (let i = 1; i < data.length; i++) out.push(data[i] * k + out[i - 1] * (1 - k));
            return out;
        };
        const e12 = ema(closes, 12);
        const e26 = ema(closes, 26);
        const line = closes.map((_, i) => e12[i] - e26[i]);
        return line[line.length - 1];
    }

    // ── Canvas chart with projection band ───────────────────────────────────

    function calcSMA(prices, period) {
        const result = [];
        for (let i = 0; i < prices.length; i++) {
            if (i < period - 1) { result.push(null); continue; }
            let sum = 0;
            for (let j = 0; j < period; j++) sum += Number(prices[i - j].Close);
            result.push(sum / period);
        }
        return result;
    }

    function renderChart() {
        const canvas = el('ml-chart');
        const tooltip = el('ml-chart-tooltip');
        if (!canvas || !priceData || !priceData.length) return;
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        const cssW = rect.width || 600, cssH = rect.height || 300;
        canvas.width = cssW * dpr;
        canvas.height = cssH * dpr;
        ctx.scale(dpr, dpr);

        const data = priceData;
        const _horizon = (prediction && prediction.horizon_days)
            || parseInt(el('lab-horizon') ? el('lab-horizon').value : '5', 10) || 5;
        const lastClose = Number(data[data.length - 1].Close);

        const closes = data.map(d => Number(d.Close)).filter(v => !isNaN(v));
        const highs = data.map(d => Number(d.High));
        const lows = data.map(d => Number(d.Low));
        const allVals = [...closes, ...highs, ...lows];
        const min = Math.min.apply(null, allVals);
        const max = Math.max.apply(null, allVals);
        const range = (max - min) || 1;
        const padL = 12, padR = 16, padT = 16, padB = 20;
        const w = cssW - padL - padR, h = cssH - padT - padB;
        const n = data.length;
        const barW = Math.max(2, (w / n) * 0.55);

        function x(i) { return padL + (i / Math.max(n - 1, 1)) * w; }
        function y(v) { return padT + h - ((v - min) / range) * h; }

        // Background.
        const bgGrad = ctx.createLinearGradient(0, 0, 0, cssH);
        bgGrad.addColorStop(0, '#fafbff');
        bgGrad.addColorStop(1, '#f0f4ff');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, cssW, cssH);

        // Subtle grid.
        ctx.strokeStyle = 'rgba(226,232,240,0.7)';
        ctx.lineWidth = 1;
        for (let g = 0; g <= 4; g++) {
            const yy = padT + (g / 4) * h;
            ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(cssW - padR, yy); ctx.stroke();
        }
        // Price axis labels.
        ctx.fillStyle = '#94a3b8';
        ctx.font = '600 10px system-ui, sans-serif';
        ctx.textAlign = 'right';
        for (let g = 0; g <= 4; g++) {
            const vv = min + (g / 4) * range;
            const yy = padT + (g / 4) * h;
            ctx.fillText('$' + vv.toFixed(0), padL - 4, yy + 3);
        }

        // ── Price area fill ──────────────────────────────────────────────────
        const pricePath = new Path2D();
        pricePath.moveTo(x(0), y(closes[0]));
        for (let i = 1; i < closes.length; i++) {
            pricePath.lineTo(x(i), y(closes[i]));
        }
        for (let i = closes.length - 1; i >= 0; i--) {
            pricePath.lineTo(x(i), y(closes[closes.length - 1]) + 10);
        }
        pricePath.closePath();
        const areaGrad = ctx.createLinearGradient(0, padT, 0, padT + h);
        areaGrad.addColorStop(0, 'rgba(59,130,246,0.12)');
        areaGrad.addColorStop(1, 'rgba(59,130,246,0.01)');
        ctx.fillStyle = areaGrad;
        ctx.fill(pricePath);

        // ── Price line ───────────────────────────────────────────────────────
        ctx.beginPath();
        ctx.strokeStyle = '#1a73e8';
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.moveTo(x(0), y(closes[0]));
        for (let i = 1; i < closes.length; i++) {
            ctx.lineTo(x(i), y(closes[i]));
        }
        ctx.stroke();

        // ── Candlesticks (last 30 only for clarity) ─────────────────────────
        const showCount = Math.min(60, data.length);
        const startIdx = data.length - showCount;
        for (let i = startIdx; i < data.length; i++) {
            const o = Number(data[i].Open), c = Number(data[i].Close);
            const hi = Number(data[i].High), lo = Number(data[i].Low);
            if (isNaN(o) || isNaN(c)) continue;
            const up = c >= o;
            const color = up ? '#10b981' : '#ef4444';
            ctx.strokeStyle = color; ctx.fillStyle = color;
            const xi = x(i);
            // wick
            ctx.beginPath();
            ctx.moveTo(xi, y(hi)); ctx.lineTo(xi, y(lo)); ctx.stroke();
            // body
            const top = y(Math.max(o, c)), bodyH = Math.max(1.5, Math.abs(y(o) - y(c)));
            ctx.fillRect(xi - barW / 2, top, barW, bodyH);
        }

        // ── SMA 20 ────────────────────────────────────────────────────────────
        const sma20 = calcSMA(data, 20);
        ctx.beginPath();
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([]);
        let started = false;
        for (let i = 0; i < sma20.length; i++) {
            if (sma20[i] === null) { started = false; continue; }
            if (!started) { ctx.moveTo(x(i), y(sma20[i])); started = true; }
            else ctx.lineTo(x(i), y(sma20[i]));
        }
        ctx.stroke();

        // ── SMA 50 ────────────────────────────────────────────────────────────
        if (data.length >= 50) {
            const sma50 = calcSMA(data, 50);
            ctx.beginPath();
            ctx.strokeStyle = '#f59e0b';
            ctx.lineWidth = 1.5;
            started = false;
            for (let i = 0; i < sma50.length; i++) {
                if (sma50[i] === null) { started = false; continue; }
                if (!started) { ctx.moveTo(x(i), y(sma50[i])); started = true; }
                else ctx.lineTo(x(i), y(sma50[i]));
            }
            ctx.stroke();
        }

        // ── Last price dot + label ───────────────────────────────────────────
        ctx.beginPath();
        ctx.arc(x(n - 1), y(lastClose), 4, 0, Math.PI * 2);
        ctx.fillStyle = '#1a73e8';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = '#1a73e8';
        ctx.font = '800 11px system-ui, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('$' + lastClose.toFixed(2), x(n - 1) + 8, y(lastClose) + 4);

        // ── Projection band ───────────────────────────────────────────────────
        if (prediction && prediction.direction) {
            const probUp = prediction.prob_up || 0;
            const probDown = prediction.prob_down || 0;
            const confidence = Math.max(probUp, probDown);
            const delta = lastClose * (probUp - probDown) * 0.08;
            const end = lastClose + delta;
            const xStart = x(n - 1);
            const xEnd = cssW - padR + 8;
            const deltaBand = Math.abs(delta) * (1 - confidence) * 1.5;

            const color = prediction.direction === 'UP' ? '#10b981'
                : prediction.direction === 'DOWN' ? '#ef4444' : '#94a3b8';

            // Show legend.
            const legProj = el('legend-proj');
            const legDot = el('legend-proj-dot');
            const legLabel = el('legend-proj-label');
            if (legProj) { legProj.style.display = 'flex'; }
            if (legDot) legDot.style.background = color;
            if (legLabel) legLabel.textContent = prediction.direction + ' Projection';

            // Gradient cone.
            const coneGrad = ctx.createLinearGradient(0, padT, 0, padT + h);
            const alpha = Math.min(0.35, confidence * 0.5);
            if (prediction.direction === 'UP') {
                coneGrad.addColorStop(0, `rgba(16,185,129,${alpha})`);
                coneGrad.addColorStop(1, `rgba(16,185,129,${alpha * 0.2})`);
            } else {
                coneGrad.addColorStop(0, `rgba(239,68,68,${alpha})`);
                coneGrad.addColorStop(1, `rgba(239,68,68,${alpha * 0.2})`);
            }

            ctx.beginPath();
            ctx.moveTo(xStart, y(lastClose));
            ctx.lineTo(xEnd, y(end + deltaBand));
            ctx.lineTo(xEnd, y(end - deltaBand));
            ctx.closePath();
            ctx.fillStyle = coneGrad;
            ctx.fill();

            // Upper and lower band edges.
            ctx.strokeStyle = color;
            ctx.globalAlpha = 0.5;
            ctx.setLineDash([4, 3]);
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(xStart, y(lastClose));
            ctx.lineTo(xEnd, y(end + deltaBand));
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(xStart, y(lastClose));
            ctx.lineTo(xEnd, y(end - deltaBand));
            ctx.stroke();
            ctx.globalAlpha = 1;
            ctx.setLineDash([]);

            // Center projection line.
            ctx.strokeStyle = color;
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.moveTo(xStart, y(lastClose));
            ctx.lineTo(xEnd, y(end));
            ctx.stroke();

            // Arrow head.
            const arrowX = xEnd, arrowY = y(end);
            ctx.fillStyle = color;
            ctx.beginPath();
            if (delta >= 0) {
                ctx.moveTo(arrowX, arrowY - 8);
                ctx.lineTo(arrowX + 6, arrowY);
                ctx.lineTo(arrowX, arrowY + 2);
            } else {
                ctx.moveTo(arrowX, arrowY + 8);
                ctx.lineTo(arrowX + 6, arrowY);
                ctx.lineTo(arrowX, arrowY - 2);
            }
            ctx.closePath();
            ctx.fill();

            // Projection label.
            ctx.fillStyle = color;
            ctx.font = '800 10px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(
                prediction.direction + ' $' + Math.abs(delta).toFixed(2),
                (xStart + xEnd) / 2,
                prediction.direction === 'UP'
                    ? Math.min(y(end + deltaBand), padT + 16)
                    : Math.max(y(end - deltaBand), padT + 28)
            );
        }

        // ── Hover tooltip ─────────────────────────────────────────────────────
        canvas.onmousemove = function(e) {
            if (!tooltip) return;
            const bx = canvas.getBoundingClientRect();
            const mx = e.clientX - bx.left;
            const my = e.clientY - bx.top;
            if (mx < padL || mx > cssW - padR) { tooltip.style.display = 'none'; return; }

            // Find nearest bar.
            const idx = Math.round(((mx - padL) / w) * (n - 1));
            if (idx < 0 || idx >= data.length) { tooltip.style.display = 'none'; return; }
            const d = data[idx];
            const up = Number(d.Close) >= Number(d.Open);
            const change = ((Number(d.Close) - Number(d.Open)) / Number(d.Open) * 100).toFixed(2);

            tooltip.innerHTML =
                '<div style="color:#94a3b8;margin-bottom:4px;">' + (d.Date ? d.Date.split('T')[0] : '—') + '</div>' +
                '<div>O <span style="color:' + (up ? '#10b981' : '#ef4444') + ';">' + Number(d.Open).toFixed(2) + '</span>  ' +
                'H <span style="color:#10b981">' + Number(d.High).toFixed(2) + '</span></div>' +
                '<div>L <span style="color:#ef4444">' + Number(d.Low).toFixed(2) + '</span>  ' +
                'C <span style="color:' + (up ? '#10b981' : '#ef4444') + ';">' + Number(d.Close).toFixed(2) + '</span>  ' +
                '<span style="color:' + (up ? '#10b981' : '#ef4444') + ';">(' + (change > 0 ? '+' : '') + change + '%)</span></div>';
            tooltip.style.display = 'block';
            const tx = Math.min(mx, cssW - 160);
            tooltip.style.left = tx + 'px';
            tooltip.style.top = (my - 70) + 'px';
        };
        canvas.onmouseleave = function() { if (tooltip) tooltip.style.display = 'none'; };
    }

    // ── Wire up events ───────────────────────────────────────────────────────

    const PRESETS = {
        baseline: { model_name: 'hist_gbm', horizon: 5, margin: 0.0, folds: 3, max_train: 200, feature_groups: null },
        trend: { model_name: 'logistic', horizon: 10, margin: 0.005, folds: 4, max_train: 400, feature_groups: ['trend', 'returns', 'volume'] },
        'long-horizon': { model_name: 'random_forest', horizon: 20, margin: 0.02, folds: 5, max_train: 300, feature_groups: ['returns', 'volatility', 'trend', 'macd'] },
    };

    function applyPreset(name) {
        const preset = PRESETS[name];
        if (!preset || !mlOptions) return;
        const knobs = {
            model_name: preset.model_name,
            horizon: preset.horizon,
            margin: preset.margin,
            folds: preset.folds,
            max_train: preset.max_train,
            feature_groups: preset.feature_groups || mlOptions.feature_groups.map(g => g.name),
        };
        applyKnobs(knobs);
        setLabStatus('Preset "' + name + '" loaded.');
        if (currentTicker) run();
    }

    function initLab() {
        const sliderIds = ['lab-horizon', 'lab-margin', 'lab-folds', 'lab-max-train'];
        sliderIds.forEach(id => {
            const node = el(id);
            if (node) node.addEventListener('input', syncKnobLabels);
        });
        // Wire original lab buttons if they exist (predictions.html)
        const labRun = el('lab-run');
        if (labRun) labRun.addEventListener('click', run);
        const labReset = el('lab-reset');
        if (labReset) labReset.addEventListener('click', () => {
            applyKnobs(mlOptions ? mlOptions.defaults : null);
            setLabStatus('Defaults restored.');
        });
        const labPresetBaseline = el('lab-preset-baseline');
        if (labPresetBaseline) labPresetBaseline.addEventListener('click', () => applyPreset('baseline'));
        const labPresetTrend = el('lab-preset-trend');
        if (labPresetTrend) labPresetTrend.addEventListener('click', () => applyPreset('trend'));
        const labPresetLong = el('lab-preset-long');
        if (labPresetLong) labPresetLong.addEventListener('click', () => applyPreset('long-horizon'));
    }

    function init() {
        // Wire up the Model Lab buttons (in the full lab panel - index.html)
        const mlLabRun = el('ml-lab-run');
        if (mlLabRun) mlLabRun.addEventListener('click', run);
        const mlLabReset = el('ml-lab-reset');
        if (mlLabReset) mlLabReset.addEventListener('click', () => {
            applyKnobs(mlOptions ? mlOptions.defaults : null);
            setLabStatus('Defaults restored.');
        });
        const mlLabPresetBaseline = el('ml-lab-preset-baseline');
        if (mlLabPresetBaseline) mlLabPresetBaseline.addEventListener('click', () => applyPreset('baseline'));
        const mlLabPresetTrend = el('ml-lab-preset-trend');
        if (mlLabPresetTrend) mlLabPresetTrend.addEventListener('click', () => applyPreset('trend'));
        const mlLabPresetLong = el('ml-lab-preset-long');
        if (mlLabPresetLong) mlLabPresetLong.addEventListener('click', () => applyPreset('long-horizon'));
        // Also wire the original lab buttons if they exist (for predictions.html compatibility)
        const labRun = el('lab-run');
        if (labRun) labRun.addEventListener('click', run);
        const mlRunBtn = el('ml-run-btn');
        if (mlRunBtn) mlRunBtn.addEventListener('click', run);
        // Initialize lab panel sliders and other elements
        initLab();
        // Load model options
        loadOptions();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
