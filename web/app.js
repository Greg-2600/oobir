// Configuration
// Prefer explicit value from config.js (window.OOBIR_API_BASE), otherwise
// derive from current host and default API port (8000).
const API_BASE_URL = (typeof window !== 'undefined' && window.OOBIR_API_BASE)
    ? window.OOBIR_API_BASE
    : (window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'http://' + window.location.hostname + ':8000');

// State
let currentTicker = '';
let fundamentalsData = {};

// DOM Elements
const landingPage = document.getElementById('landing-page');
const resultsPage = document.getElementById('results-page');
const searchForm = document.getElementById('search-form');
const searchFormCompact = document.getElementById('search-form-compact');
const tickerInput = document.getElementById('ticker-input');
const tickerInputCompact = document.getElementById('ticker-input-compact');
const backButton = document.getElementById('back-button');
const errorMessage = document.getElementById('error-message');
const loadingSpinner = document.getElementById('loading-spinner');
const loadingTicker = document.getElementById('loading-ticker');
const resultsContainer = document.getElementById('results-container');

// Event Listeners
searchForm.addEventListener('submit', handleSearch);
searchFormCompact.addEventListener('submit', handleSearch);
backButton.addEventListener('click', showLandingPage);

// Technical Indicator Calculations
function calculateSMA(prices, period) {
    const result = new Array(prices.length).fill(null);
    for (let i = period - 1; i < prices.length; i++) {
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += prices[i - j].Close;
        }
        result[i] = sum / period;
    }
    return result;
}

function calculateBollingerBands(prices, period, stdDevMultiplier) {
    const sma = calculateSMA(prices, period);
    const upper = new Array(prices.length).fill(null);
    const lower = new Array(prices.length).fill(null);
    const middle = sma;
    
    for (let i = period - 1; i < prices.length; i++) {
        if (sma[i] === null) continue;
        
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += Math.pow(prices[i - j].Close - sma[i], 2);
        }
        const stdDev = Math.sqrt(sum / period);
        upper[i] = sma[i] + (stdDev * stdDevMultiplier);
        lower[i] = sma[i] - (stdDev * stdDevMultiplier);
    }
    
    return { upper, lower, middle };
}

// Technical indicators
function calculateRSI(prices, period = 14) {
    const rsi = new Array(prices.length).fill(null);
    for (let i = period; i < prices.length; i++) {
        let gains = 0;
        let losses = 0;
        for (let j = i - period + 1; j <= i; j++) {
            const change = prices[j].Close - prices[j - 1].Close;
            if (change > 0) gains += change;
            else losses += Math.abs(change);
        }
        const avgGain = gains / period;
        const avgLoss = losses / period;
        if (avgLoss === 0) {
            rsi[i] = 100;
        } else {
            const rs = avgGain / avgLoss;
            rsi[i] = 100 - (100 / (1 + rs));
        }
    }
    return rsi;
}

function calculateEMA(values, period) {
    const ema = new Array(values.length).fill(null);
    const multiplier = 2 / (period + 1);
    for (let i = 0; i < values.length; i++) {
        if (values[i] === null || values[i] === undefined) {
            ema[i] = null;
            continue;
        }
        if (i === 0 || ema[i - 1] === null) {
            ema[i] = values[i];
        } else {
            ema[i] = (values[i] - ema[i - 1]) * multiplier + ema[i - 1];
        }
    }
    return ema;
}

function calculateMACD(prices, fast = 12, slow = 26, signal = 9) {
    const closes = prices.map(p => p.Close);
    const emaFast = calculateEMA(closes, fast);
    const emaSlow = calculateEMA(closes, slow);
    const macdLine = emaFast.map((val, idx) => {
        if (val === null || emaSlow[idx] === null) return null;
        return val - emaSlow[idx];
    });
    const signalLine = calculateEMA(macdLine, signal);
    const histogram = macdLine.map((val, idx) => {
        if (val === null || signalLine[idx] === null) return null;
        return val - signalLine[idx];
    });
    return { macdLine, signalLine, histogram };
}

function calculateStochastic(prices, period = 14) {
    const stoch = new Array(prices.length).fill(null);
    for (let i = period - 1; i < prices.length; i++) {
        const window = prices.slice(i - period + 1, i + 1);
        const high = Math.max(...window.map(p => p.High));
        const low = Math.min(...window.map(p => p.Low));
        const close = prices[i].Close;
        stoch[i] = ((close - low) / Math.max(high - low, 1e-9)) * 100;
    }
    return stoch;
}

function calculateADX(prices, period = 14) {
    const tr = [];
    const plusDM = [];
    const minusDM = [];
    for (let i = 1; i < prices.length; i++) {
        const highDiff = prices[i].High - prices[i - 1].High;
        const lowDiff = prices[i - 1].Low - prices[i].Low;
        plusDM.push(highDiff > lowDiff && highDiff > 0 ? highDiff : 0);
        minusDM.push(lowDiff > highDiff && lowDiff > 0 ? lowDiff : 0);
        tr.push(Math.max(
            prices[i].High - prices[i].Low,
            Math.abs(prices[i].High - prices[i - 1].Close),
            Math.abs(prices[i].Low - prices[i - 1].Close)
        ));
    }
    const atr = calculateEMA(tr, period).map(v => v === null ? null : v);
    const plusDI = atr.map((v, idx) => v ? (calculateEMA(plusDM, period)[idx] / v) * 100 : null);
    const minusDI = atr.map((v, idx) => v ? (calculateEMA(minusDM, period)[idx] / v) * 100 : null);
    const dx = plusDI.map((p, idx) => {
        if (p === null || minusDI[idx] === null) return null;
        return Math.abs(p - minusDI[idx]) / Math.max(p + minusDI[idx], 1e-9) * 100;
    });
    return calculateEMA(dx, period);
}

// Handle search submission
function handleSearch(e) {
    e.preventDefault();
    const ticker = (e.target === searchForm ? tickerInput : tickerInputCompact).value.trim().toUpperCase();
    
    if (!ticker) {
        showError('Please enter a stock ticker');
        return;
    }
    
    if (!/^[A-Z0-9\-\^]{1,10}$/.test(ticker)) {
        showError('Please enter a valid stock ticker (1-10 characters, letters, numbers, -, ^)');
        return;
    }
    
    hideError();
    currentTicker = ticker;
    loadStockData(ticker);
}

// Show landing page
function showLandingPage() {
    landingPage.classList.remove('hidden');
    resultsPage.classList.add('hidden');
    tickerInput.value = '';
    tickerInput.focus();
}

// Show results page
function showResultsPage() {
    landingPage.classList.add('hidden');
    resultsPage.classList.remove('hidden');
    loadingSpinner.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
}

// Show/hide error messages
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

function hideError() {
    errorMessage.classList.remove('show');
}

// Load all stock data
async function loadStockData(ticker) {
    showResultsPage();
    loadingTicker.textContent = ticker;
    tickerInputCompact.value = ticker;
    
    // Update stock header
    document.getElementById('stock-symbol').textContent = ticker;
    
    // Initialize AI sections with buttons
    initializeAIRecommendation(ticker);
    initializeNewsSentiment(ticker);
    initializeTechnicalAnalysis(ticker);
    
    // Load all data concurrently
    const dataPromises = {
        fundamentals: fetchData(`/api/fundamentals/${ticker}`, 'fundamentals-data', renderFundamentals),
        priceHistory: fetchData(`/api/price-history/${ticker}`, 'price-history-data', renderPriceHistory),
        analystTargets: fetchData(`/api/analyst-targets/${ticker}`, 'analyst-targets-data', renderAnalystTargets),
        calendar: fetchData(`/api/calendar/${ticker}`, 'calendar-data', renderCalendar),
        incomeStmt: fetchData(`/api/income-stmt/${ticker}`, 'income-stmt-data', renderIncomeStatement),
        balanceSheet: fetchData(`/api/balance-sheet/${ticker}`, 'balance-sheet-data', renderBalanceSheet),
        news: fetchData(`/api/news/${ticker}`, 'news-data', renderNews),
        optionChain: fetchData(`/api/option-chain/${ticker}`, 'option-chain-data', renderOptionChain)
    };
    
    // Wait for all data to load
    await Promise.allSettled(Object.values(dataPromises));
    const techContainer = document.getElementById('technical-signals-data');
    if (techContainer) {
        renderTechnicalSignals(null, techContainer);
    }
    
    // Show results
    loadingSpinner.classList.add('hidden');
    resultsContainer.classList.remove('hidden');
}

// Initialize AI recommendation with button
function initializeAIRecommendation(ticker) {
    const container = document.getElementById('ai-recommendation');
    container.innerHTML = `
        <button class="ai-button" onclick="loadAIRecommendation('${ticker}')">
            🤖 Get AI Recommendation
        </button>
    `;
}

// Load AI recommendation on demand
async function loadAIRecommendation(ticker) {
    const container = document.getElementById('ai-recommendation');
    container.innerHTML = '<p class="text-muted">🔄 Loading AI recommendation...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/ai/action-recommendation/${ticker}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        renderAIRecommendation(data, container);
    } catch (error) {
        console.error(`Error fetching AI recommendation:`, error);
        container.innerHTML = `
            <p class="text-danger">❌ Failed to load AI recommendation</p>
            <button class="ai-button" onclick="loadAIRecommendation('${ticker}')" style="margin-top: 10px;">
                🔄 Retry
            </button>
        `;
    }
}

// Load AI selected stocks card on results page
// Initialize news sentiment with button
function initializeNewsSentiment(ticker) {
    const container = document.getElementById('news-sentiment-data');
    container.innerHTML = `
        <button class="ai-button" onclick="loadNewsSentiment('${ticker}')">
            📰 Get News & Sentiment Analysis
        </button>
    `;
}

// Load news sentiment on demand
async function loadNewsSentiment(ticker) {
    const container = document.getElementById('news-sentiment-data');
    container.innerHTML = '<p class="text-muted">🔄 Loading news sentiment...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/ai/news-sentiment/${ticker}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        renderNewsSentiment(data, container);
    } catch (error) {
        console.error(`Error fetching news sentiment:`, error);
        container.innerHTML = `
            <p class="text-danger">❌ Failed to load news sentiment</p>
            <button class="ai-button" onclick="loadNewsSentiment('${ticker}')" style="margin-top: 10px;">
                🔄 Retry
            </button>
        `;
    }
}

// Initialize technical analysis button
function initializeTechnicalAnalysis(ticker) {
    const container = document.getElementById('technical-analysis-data');
    container.innerHTML = `
        <button class="ai-button" onclick="loadTechnicalAnalysis('${ticker}')">
            📊 Get Technical Analysis
        </button>
    `;
}

// Load technical analysis on demand
async function loadTechnicalAnalysis(ticker) {
    const container = document.getElementById('technical-analysis-data');
    container.innerHTML = '<p class="text-muted">🔄 Loading technical analysis...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/ai/technical-analysis/${ticker}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        renderTechnicalAnalysis(data, container);
    } catch (error) {
        console.error(`Error fetching technical analysis:`, error);
        container.innerHTML = `
            <p class="text-danger">❌ Failed to load technical analysis</p>
            <button class="ai-button" onclick="loadTechnicalAnalysis('${ticker}')" style="margin-top: 10px;">
                🔄 Retry
            </button>
        `;
    }
}

// Generic fetch function
async function fetchData(endpoint, containerId, renderFunction) {
    const container = document.getElementById(containerId);
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        renderFunction(data, container);
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        container.innerHTML = `<p class="text-danger">❌ Failed to load data</p>`;
    }
}

// Utility to hide card if no data
function hideCardIfEmpty(container) {
    const card = container.closest('.card');
    if (card) {
        card.style.display = 'none';
    }
}

// Render functions
function renderFundamentals(data, container) {
    console.log('renderFundamentals called with:', data);
    if (!data || typeof data !== 'object') {
        hideCardIfEmpty(container);
        return;
    }
    
    // Store fundamentals globally for use in other renderers
    fundamentalsData = data;
    
    // Set company name and industry/sector in header if available
    const companyName = data.longName || data.shortName || data.long_name || data.short_name || '';
    const sector = data.sector || data.Sector || '';
    const industry = data.industry || data.Industry || '';
    
    const nameEl = document.getElementById('company-name');
    if (nameEl) {
        nameEl.textContent = companyName;
    }
    
    // Add sector/industry info in header
    const summaryEl = document.getElementById('company-summary');
    if (summaryEl) {
        let summary = '';
        if (sector || industry) {
            summary = [sector, industry].filter(s => s).join(' • ');
        }
        summaryEl.textContent = summary;
    }
    
    // Populate company summary box
    const summaryBox = document.getElementById('summary-content');
    if (summaryBox) {
        const description = data.longBusinessSummary || data.businessSummary || '';
        const website = data.website || '';
        const employees = data.fullTimeEmployees || data.employees || '';
        const ceo = data.companyOfficers?.[0]?.name || '';
        const headquarters = data.city || '';
        const state = data.state || '';
        const country = data.country || '';
        
        const locationStr = [headquarters, state, country].filter(s => s).join(', ');
        
        let html = '';
        if (description) {
            html += `<p style="margin-bottom: 12px;">${escapeHtml(description)}</p>`;
        }
        
        const infoItems = [];
        if (website) {
            infoItems.push(`<strong>Website:</strong> <a href="${escapeHtml(website)}" target="_blank" style="color: #3b82f6;">${escapeHtml(website)}</a>`);
        }
        if (employees) {
            infoItems.push(`<strong>Employees:</strong> ${Number(employees).toLocaleString()}`);
        }
        if (ceo) {
            infoItems.push(`<strong>CEO:</strong> ${escapeHtml(ceo)}`);
        }
        if (locationStr) {
            infoItems.push(`<strong>Location:</strong> ${escapeHtml(locationStr)}`);
        }
        
        if (infoItems.length > 0) {
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px;">' +
                infoItems.map(item => `<div>${item}</div>`).join('') +
                '</div>';
        }
        
        summaryBox.innerHTML = html || '<p class="text-muted">No company information available</p>';
    }
    
    const fields = {
        'Market Cap': formatLargeNumber(data.marketCap || data.market_cap),
        'P/E Ratio': formatNumber(data.trailingPE || data.trailing_pe),
        'Forward P/E': formatNumber(data.forwardPE || data.forward_pe),
        'PEG Ratio': formatNumber(data.pegRatio || data.peg_ratio),
        'Price/Book': formatNumber(data.priceToBook || data.price_to_book),
        'Dividend Yield': formatPercent(data.dividendYield || data.dividend_yield),
        '52 Week High': formatCurrency(data.fiftyTwoWeekHigh || data.fifty_two_week_high),
        '52 Week Low': formatCurrency(data.fiftyTwoWeekLow || data.fifty_two_week_low)
    };
    
    renderTable(fields, container);
}

function renderPriceHistory(data, container) {
    console.log('renderPriceHistory called with:', data);
    if (!data || !data.data || !Array.isArray(data.data)) {
        console.log('Price history data validation failed');
        container.innerHTML = '<p class="text-muted">No price history available</p>';
        return;
    }
    
    const prices = data.data;
    const latest = prices[prices.length - 1];
    const oldest = prices[0];
    window.currentPrice = latest.Close;
    
    // Calculate trend metrics
    const calcPctChange = (periodDays) => {
        if (prices.length < periodDays) return null;
        const periodStart = prices[prices.length - periodDays];
        return ((latest.Close - periodStart.Close) / periodStart.Close) * 100;
    };
    
    const change1D = prices.length >= 2 ? ((latest.Close - prices[prices.length - 2].Close) / prices[prices.length - 2].Close) * 100 : null;
    const change1W = calcPctChange(5);
    const change1M = calcPctChange(21);
    
    const avgVolume = prices.reduce((sum, p) => sum + (p.Volume || 0), 0) / prices.length;
    const currentVolume = latest.Volume || 0;
    const volumeChange = ((currentVolume - avgVolume) / avgVolume) * 100;
    
    const trendHtml = `
        <div style="display: flex; gap: 20px; line-height: 1.6;">
            <div>
                <strong>Price Change</strong><br>
                ${change1D !== null ? `<span style="color: ${change1D >= 0 ? '#22c55e' : '#ef4444'};">1D: ${change1D >= 0 ? '▲' : '▼'} ${Math.abs(change1D).toFixed(2)}%</span><br>` : ''}
                ${change1W !== null ? `<span style="color: ${change1W >= 0 ? '#22c55e' : '#ef4444'};">1W: ${change1W >= 0 ? '▲' : '▼'} ${Math.abs(change1W).toFixed(2)}%</span><br>` : ''}
                ${change1M !== null ? `<span style="color: ${change1M >= 0 ? '#22c55e' : '#ef4444'};">1M: ${change1M >= 0 ? '▲' : '▼'} ${Math.abs(change1M).toFixed(2)}%</span>` : ''}
            </div>
            <div style="border-left: 1px solid #ddd; padding-left: 20px;">
                <strong>52W Range</strong><br>
                <span style="font-size: 0.85em;">High: ${fundamentalsData.fiftyTwoWeekHigh ? formatCurrency(fundamentalsData.fiftyTwoWeekHigh) : 'N/A'}</span><br>
                <span style="font-size: 0.85em;">Low: ${fundamentalsData.fiftyTwoWeekLow ? formatCurrency(fundamentalsData.fiftyTwoWeekLow) : 'N/A'}</span>
            </div>
            <div style="border-left: 1px solid #ddd; padding-left: 20px;">
                <strong>Volume</strong><br>
                <span style="font-size: 0.85em; color: ${volumeChange >= 0 ? '#22c55e' : '#ef4444'};">
                    ${volumeChange >= 0 ? '▲' : '▼'} ${Math.abs(volumeChange).toFixed(0)}% vs avg
                </span>
            </div>
        </div>
    `;
    
    const trendEl = document.getElementById('price-trend-summary');
    if (trendEl) {
        trendEl.innerHTML = trendHtml;
    }
    
    // Show latest price prominently
    document.getElementById('stock-price').innerHTML = `
        <strong>${formatCurrency(latest.Close)}</strong>
        <span class="${latest.Close >= oldest.Close ? 'text-success' : 'text-danger'}">
            ${latest.Close >= oldest.Close ? '▲' : '▼'} 
            ${formatPercent((latest.Close - oldest.Close) / oldest.Close)} (121d)
        </span>
    `;
    
    // Calculate price range for scaling
    const minPrice = Math.min(...prices.map(p => p.Low));
    const maxPrice = Math.max(...prices.map(p => p.High));
    const range = maxPrice - minPrice;
    
    // Calculate volume range for scaling
    const maxVolume = Math.max(...prices.map(p => p.Volume || 0));
    
    // Calculate technical indicators
    const sma20 = calculateSMA(prices, 20);
    const sma50 = calculateSMA(prices, 50);
    const { upper: bbUpper, lower: bbLower } = calculateBollingerBands(prices, 20, 2);
    const rsi = calculateRSI(prices, 14);
    const { macdLine, signalLine, histogram } = calculateMACD(prices, 12, 26, 9);
    const stoch = calculateStochastic(prices, 14);
    const adx = calculateADX(prices, 14);
    
    window.technicalIndicators = {
        rsi: rsi[rsi.length - 1],
        macd: macdLine[macdLine.length - 1],
        macdSignal: signalLine[signalLine.length - 1],
        macdHistogram: histogram[histogram.length - 1],
        stochastic: stoch[stoch.length - 1],
        adx: adx[adx.length - 1],
        sma20: sma20[sma20.length - 1],
        sma50: sma50[sma50.length - 1],
        bbUpper: bbUpper[bbUpper.length - 1],
        bbLower: bbLower[bbLower.length - 1]
    };
    
    // Create candlestick chart with technical indicators
    const chartHtml = `
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <!-- Legend -->
            <div style="display: flex; gap: 20px; font-size: 0.85em; flex-wrap: wrap;">
                <div><span style="display: inline-block; width: 12px; height: 2px; background: #22c55e; margin-right: 4px;"></span>Green = Up</div>
                <div><span style="display: inline-block; width: 12px; height: 2px; background: #ef4444; margin-right: 4px;"></span>Red = Down</div>
                <div><span style="display: inline-block; width: 12px; height: 2px; background: #3b82f6; margin-right: 4px;"></span>SMA 20</div>
                <div><span style="display: inline-block; width: 12px; height: 2px; background: #f59e0b; margin-right: 4px;"></span>SMA 50</div>
                <div><span style="display: inline-block; width: 12px; height: 1px; background: #a78bfa; margin-right: 4px;"></span>Bollinger Bands</div>
            </div>
            
            <!-- Chart -->
            <div style="display: flex; flex-direction: column; gap: 0;">
                <div style="display: flex; align-items: flex-end; justify-content: space-around; gap: 2px; height: 280px; padding: 10px; background: #f9f9f9; border-radius: 4px 4px 0 0; position: relative;">
                    ${prices.map((day, idx) => {
                        const open = day.Open;
                        const close = day.Close;
                        const high = day.High;
                        const low = day.Low;
                        
                        // Normalize to 0-100 scale
                        const highPercent = ((high - minPrice) / range) * 100;
                        const lowPercent = ((low - minPrice) / range) * 100;
                        const openPercent = ((open - minPrice) / range) * 100;
                        const closePercent = ((close - minPrice) / range) * 100;
                        
                        // Technical indicators positioning
                        const sma20Percent = sma20[idx] ? ((sma20[idx] - minPrice) / range) * 100 : null;
                        const sma50Percent = sma50[idx] ? ((sma50[idx] - minPrice) / range) * 100 : null;
                        const bbUpperPercent = bbUpper[idx] ? ((bbUpper[idx] - minPrice) / range) * 100 : null;
                        const bbLowerPercent = bbLower[idx] ? ((bbLower[idx] - minPrice) / range) * 100 : null;
                        
                        // Determine color (green for up, red for down)
                        const isUp = close >= open;
                        const color = isUp ? '#22c55e' : '#ef4444';
                        
                        // Body is between open and close
                        const bodyTop = Math.min(openPercent, closePercent);
                        const bodyHeight = Math.abs(closePercent - openPercent) || 1;
                        const wickTop = lowPercent;
                        const wickHeight = highPercent - lowPercent;
                        
                        // Build indicator HTML
                        let indicatorHtml = '';
                        if (bbUpperPercent && bbLowerPercent) {
                            indicatorHtml += '<div style="position: absolute; bottom: ' + bbLowerPercent + '%; width: 100%; height: ' + (bbUpperPercent - bbLowerPercent) + '%; background: rgba(167, 139, 250, 0.1); border-top: 0.5px solid rgba(167, 139, 250, 0.5); border-bottom: 0.5px solid rgba(167, 139, 250, 0.5);"></div>';
                        }
                        if (sma50Percent) {
                            indicatorHtml += '<div style="position: absolute; bottom: ' + sma50Percent + '%; width: 100%; height: 1px; background: #f59e0b;"></div>';
                        }
                        if (sma20Percent) {
                            indicatorHtml += '<div style="position: absolute; bottom: ' + sma20Percent + '%; width: 100%; height: 1px; background: #3b82f6;"></div>';
                        }
                        
                        return '<div style="flex: 1; position: relative; height: 100%;" title="' + day.Date + ': O:$' + open.toFixed(2) + ' H:$' + high.toFixed(2) + ' L:$' + low.toFixed(2) + ' C:$' + close.toFixed(2) + '">' +
                            indicatorHtml +
                            '<div style="position: absolute; bottom: ' + wickTop + '%; width: 2px; height: ' + wickHeight + '%; background: ' + color + '; left: 50%; transform: translateX(-50%);"></div>' +
                            '<div style="position: absolute; bottom: ' + bodyTop + '%; width: 100%; height: ' + bodyHeight + '%; background: ' + color + '; opacity: 0.8; border: 1px solid ' + color + ';"></div>' +
                            '</div>';
                    }).join('')}
                </div>
                <!-- Date Labels -->
                <div style="display: flex; justify-content: space-around; gap: 2px; padding: 4px 10px; background: #f9f9f9; border-radius: 0 0 4px 4px; font-size: 0.75em; color: #666;">
                    ${(() => {
                        const labels = [];
                        const step = Math.max(1, Math.floor(prices.length / 8)); // Show ~8 dates
                        for (let i = 0; i < prices.length; i += step) {
                            const dateStr = prices[i].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        // Always show last date
                        if ((prices.length - 1) % step !== 0) {
                            const dateStr = prices[prices.length - 1].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        return labels.join('');
                    })()}
                </div>
            </div>
            
            <!-- Volume Chart -->
            <div style="display: flex; flex-direction: column; gap: 0; margin-top: 4px;">
                <div style="display: flex; align-items: flex-end; justify-content: space-around; gap: 2px; height: 80px; padding: 10px; background: #f9f9f9; border-radius: 4px 4px 0 0;">
                    ${prices.map((day) => {
                        const volume = day.Volume || 0;
                        const volumePercent = maxVolume > 0 ? (volume / maxVolume) * 100 : 0;
                        const isUp = day.Close >= day.Open;
                        const color = isUp ? 'rgba(34, 197, 94, 0.6)' : 'rgba(239, 68, 68, 0.6)';
                        
                        return '<div style="flex: 1; position: relative; height: 100%;" title="' + day.Date + ': Volume ' + volume.toLocaleString() + '">' +
                            '<div style="position: absolute; bottom: 0; width: 100%; height: ' + volumePercent + '%; background: ' + color + ';"></div>' +
                            '</div>';
                    }).join('')}
                </div>
                <!-- Date Labels for Volume -->
                <div style="display: flex; justify-content: space-around; gap: 2px; padding: 4px 10px; background: #f9f9f9; border-radius: 0 0 4px 4px; font-size: 0.75em; color: #666;">
                    ${(() => {
                        const labels = [];
                        const step = Math.max(1, Math.floor(prices.length / 8));
                        for (let i = 0; i < prices.length; i += step) {
                            const dateStr = prices[i].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        if ((prices.length - 1) % step !== 0) {
                            const dateStr = prices[prices.length - 1].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        return labels.join('');
                    })()}
                </div>
            </div>
            
            <!-- RSI Oscillator -->
            <div style="padding: 10px; background: #f9f9f9; border-radius: 4px;">
                <div style="font-size: 0.9em; margin-bottom: 4px; font-weight: 600;">RSI (14)</div>
                <div style="position: relative; height: 70px; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc;">
                    <div style="position: absolute; top: 20%; width: 100%; height: 1px; background: rgba(239, 68, 68, 0.3);"></div>
                    <div style="position: absolute; bottom: 20%; width: 100%; height: 1px; background: rgba(34, 197, 94, 0.3);"></div>
                    <div style="display: flex; align-items: flex-end; height: 100%; gap: 1px;">
                        ${rsi.map((val, idx) => {
                            if (val === null) return '<div style="flex: 1;"></div>';
                            const color = val > 70 ? '#ef4444' : val < 30 ? '#22c55e' : '#6b7280';
                            return '<div style="flex: 1; height: ' + val + '%; background: ' + color + '; opacity: 0.7;" title="' + prices[idx].Date + ': RSI ' + val.toFixed(1) + '"></div>';
                        }).join('')}
                    </div>
                </div>
                <!-- Date Labels for RSI -->
                <div style="display: flex; justify-content: space-around; gap: 1px; padding: 2px 0; font-size: 0.65em; color: #999; margin-top: 2px;">
                    ${(() => {
                        const labels = [];
                        const step = Math.max(1, Math.floor(rsi.length / 8));
                        for (let i = 0; i < rsi.length; i += step) {
                            const dateStr = prices[i].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        if ((rsi.length - 1) % step !== 0) {
                            const dateStr = prices[rsi.length - 1].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        return labels.join('');
                    })()}
                </div>
            </div>
            
            <!-- MACD Histogram -->
            <div style="padding: 10px; background: #f9f9f9; border-radius: 4px;">
                <div style="font-size: 0.9em; margin-bottom: 4px; font-weight: 600;">MACD Histogram</div>
                <div style="position: relative; height: 70px; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc; display: flex; align-items: center;">
                    <div style="position: absolute; top: 50%; width: 100%; height: 1px; background: #bbb;"></div>
                    <div style="display: flex; align-items: center; width: 100%; gap: 1px;">
                        ${(() => {
                            const maxHist = Math.max(...histogram.filter(v => v !== null).map(v => Math.abs(v)), 0.0001);
                            return histogram.map((val, idx) => {
                                if (val === null) return '<div style="flex: 1;"></div>';
                                const h = (Math.abs(val) / maxHist) * 50;
                                const color = val >= 0 ? '#22c55e' : '#ef4444';
                                return '<div style="flex: 1; display: flex; align-items: flex-end; justify-content: center; height: 100%;"><div style="width: 100%; height: ' + h + '%; background: ' + color + '; opacity: 0.75;" title="' + prices[idx].Date + ': ' + val.toFixed(3) + '"></div></div>';
                            }).join('');
                        })()}
                    </div>
                </div>
                <!-- Date Labels for MACD -->
                <div style="display: flex; justify-content: space-around; gap: 1px; padding: 2px 0; font-size: 0.65em; color: #999; margin-top: 2px;">
                    ${(() => {
                        const labels = [];
                        const step = Math.max(1, Math.floor(histogram.length / 8));
                        for (let i = 0; i < histogram.length; i += step) {
                            const dateStr = prices[i].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        if ((histogram.length - 1) % step !== 0) {
                            const dateStr = prices[histogram.length - 1].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        return labels.join('');
                    })()}
                </div>
            </div>
            
            <!-- Stochastic Oscillator -->
            <div style="padding: 10px; background: #f9f9f9; border-radius: 4px;">
                <div style="font-size: 0.9em; margin-bottom: 4px; font-weight: 600;">Stochastic (14)</div>
                <div style="position: relative; height: 70px; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc;">
                    <div style="position: absolute; top: 20%; width: 100%; height: 1px; background: rgba(239, 68, 68, 0.3);"></div>
                    <div style="position: absolute; bottom: 20%; width: 100%; height: 1px; background: rgba(34, 197, 94, 0.3);"></div>
                    <div style="display: flex; align-items: flex-end; height: 100%; gap: 1px;">
                        ${stoch.map((val, idx) => {
                            if (val === null) return '<div style="flex: 1;"></div>';
                            const color = val > 80 ? '#ef4444' : val < 20 ? '#22c55e' : '#6b7280';
                            return '<div style="flex: 1; height: ' + val + '%; background: ' + color + '; opacity: 0.7;" title="' + prices[idx].Date + ': ' + val.toFixed(1) + '"></div>';
                        }).join('')}
                    </div>
                </div>
                <!-- Date Labels for Stochastic -->
                <div style="display: flex; justify-content: space-around; gap: 1px; padding: 2px 0; font-size: 0.65em; color: #999; margin-top: 2px;">
                    ${(() => {
                        const labels = [];
                        const step = Math.max(1, Math.floor(stoch.length / 8));
                        for (let i = 0; i < stoch.length; i += step) {
                            const dateStr = prices[i].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        if ((stoch.length - 1) % step !== 0) {
                            const dateStr = prices[stoch.length - 1].Date;
                            const [year, month, day] = dateStr.split('-');
                            labels.push('<div style="flex: 1; text-align: center;">' + month + '/' + day + '</div>');
                        }
                        return labels.join('');
                    })()}
                </div>
            </div>
            
            <!-- Stats -->
            <div style="text-align: center; margin-top: 16px; font-size: 0.9em; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                <div><strong>Latest Close:</strong> ${formatCurrency(latest.Close)}</div>
                <div><strong>High:</strong> ${formatCurrency(maxPrice)}</div>
                <div><strong>Low:</strong> ${formatCurrency(minPrice)}</div>
                <div><strong>SMA 20:</strong> ${formatCurrency(sma20[sma20.length - 1] || 0)}</div>
                <div><strong>SMA 50:</strong> ${formatCurrency(sma50[sma50.length - 1] || 0)}</div>
                <div><strong>RSI:</strong> ${rsi[rsi.length - 1] ? rsi[rsi.length - 1].toFixed(1) : 'N/A'}</div>
                <div><strong>MACD Hist:</strong> ${histogram[histogram.length - 1] ? histogram[histogram.length - 1].toFixed(3) : 'N/A'}</div>
                <div><strong>Stoch:</strong> ${stoch[stoch.length - 1] ? stoch[stoch.length - 1].toFixed(1) : 'N/A'}</div>
                <div><strong>ADX:</strong> ${adx[adx.length - 1] ? adx[adx.length - 1].toFixed(1) : 'N/A'}</div>
            </div>
        </div>
    `;
    
    container.innerHTML = chartHtml;
}

function renderAnalystTargets(data, container) {
    if (!data || typeof data !== 'object') {
        hideCardIfEmpty(container);
        return;
    }
    
    const fields = {
        'Current Price': formatCurrency(data.current || data.currentPrice || data.current_price),
        'Target High': formatCurrency(data.high || data.targetHighPrice || data.target_high_price),
        'Target Mean': formatCurrency(data.mean || data.targetMeanPrice || data.target_mean_price),
        'Target Low': formatCurrency(data.low || data.targetLowPrice || data.target_low_price),
        'Target Median': formatCurrency(data.median || data.targetMedianPrice || data.target_median_price)
    };
    
    renderTable(fields, container);
}

function renderCalendar(data, container) {
    if (!data || typeof data !== 'object') {
        container.innerHTML = '<p class="text-muted">No upcoming events</p>';
        return;
    }
    
    // Build event list from calendar data
    const events = [];
    if (data['Dividend Date']) {
        events.push({ event: '💰 Dividend Date', date: data['Dividend Date'] });
    }
    if (data['Ex-Dividend Date']) {
        events.push({ event: '📅 Ex-Dividend Date', date: data['Ex-Dividend Date'] });
    }
    if (data['Earnings Date'] && Array.isArray(data['Earnings Date']) && data['Earnings Date'].length > 0) {
        events.push({ event: '📊 Earnings Date', date: data['Earnings Date'][0] });
    }
    
    if (events.length === 0) {
        hideCardIfEmpty(container);
        return;
    }
    
    const html = events.map(event => `
        <div class="news-item">
            <div class="news-title">${event.event}</div>
            <div class="news-meta">${event.date}</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function renderIncomeStatement(data, container) {
    if (!data || typeof data !== 'object') {
        hideCardIfEmpty(container);
        return;
    }
    
    // Extract most recent quarter (first date key)
    const dates = Object.keys(data);
    if (dates.length === 0) {
        container.innerHTML = '<p class="text-muted">No income statement available</p>';
        return;
    }
    const latestData = data[dates[0]];
    
    const fields = {
        'Revenue': formatLargeNumber(latestData['Total Revenue'] || latestData.totalRevenue || latestData.total_revenue),
        'Gross Profit': formatLargeNumber(latestData['Gross Profit'] || latestData.grossProfit || latestData.gross_profit),
        'Operating Income': formatLargeNumber(latestData['Operating Income'] || latestData.operatingIncome || latestData.operating_income),
        'Net Income': formatLargeNumber(latestData['Net Income'] || latestData.netIncome || latestData.net_income),
        'EPS': formatNumber(latestData['Basic EPS'] || latestData.basicEPS || latestData.basic_eps),
        'EBITDA': formatLargeNumber(latestData.EBITDA || latestData.ebitda)
    };
    
    renderTable(fields, container);
}

function renderBalanceSheet(data, container) {
    if (!data || typeof data !== 'object') {
        hideCardIfEmpty(container);
        return;
    }
    
    // Extract most recent quarter (first date key)
    const dates = Object.keys(data);
    if (dates.length === 0) {
        container.innerHTML = '<p class="text-muted">No balance sheet available</p>';
        return;
    }
    const latestData = data[dates[0]];
    
    const fields = {
        'Total Assets': formatLargeNumber(latestData['TotalAssets'] || latestData['Total Assets'] || latestData.totalAssets || latestData.total_assets),
        'Total Liabilities': formatLargeNumber(latestData['TotalLiabilitiesNetMinorityInterest'] || latestData['Total Liabilities Net Minority Interest'] || latestData.totalLiabilitiesNetMinorityInterest || latestData.total_liabilities),
        'Cash': formatLargeNumber(latestData['CashAndCashEquivalents'] || latestData['Cash And Cash Equivalents'] || latestData.cashAndCashEquivalents || latestData.cash),
        'Total Debt': formatLargeNumber(latestData['TotalDebt'] || latestData['Total Debt'] || latestData.totalDebt || latestData.total_debt),
        'Stockholders Equity': formatLargeNumber(latestData['StockholdersEquity'] || latestData['Stockholders Equity'] || latestData.stockholdersEquity || latestData.stockholders_equity)
    };
    
    renderTable(fields, container);
}

function renderNews(data, container) {
    const items = Array.isArray(data) ? data : (data?.result || data?.news || []);
    if (!items || items.length === 0) {
        hideCardIfEmpty(container);
        return;
    }
    
    const html = items.slice(0, 5).map(item => {
        const content = item.content || item; // Yahoo sometimes nests under content
        const title = content.title || content.headline || item.title || item.headline || 'No title';
        const source = (content.provider?.displayName || content.provider || item.publisher || item.source || 'Unknown source');
        const link = (content.canonicalUrl?.url || content.clickThroughUrl?.url || content.link || item.link || item.url || '#');
        
        let dateStr = '';
        const ts = content.pubDate || content.publish_time || item.pubDate || item.providerPublishTime;
        if (ts) {
            const d = new Date(ts);
            if (!isNaN(d.getTime())) {
                dateStr = d.toLocaleDateString();
            }
        }
        
        return `<div class="news-item">
            <a href="${escapeHtml(link)}" target="_blank" class="news-title">${escapeHtml(title)}</a>
            <div class="news-meta">${escapeHtml(source)}${dateStr ? ' • ' + escapeHtml(dateStr) : ''}</div>
        </div>`;
    }).join('');
    
    container.innerHTML = html;
}

function renderOptionChain(data, container) {
    const toRowsFromColumns = (columns, side) => {
        if (!columns || typeof columns !== 'object') return [];
        const indices = new Set();
        Object.values(columns).forEach(col => {
            if (col && typeof col === 'object') {
                Object.keys(col).forEach(idx => indices.add(idx));
            }
        });
        return Array.from(indices)
            .sort((a, b) => Number(a) - Number(b))
            .map(idx => {
                const row = {};
                Object.entries(columns).forEach(([key, values]) => {
                    if (values && typeof values === 'object' && idx in values) {
                        row[key] = values[idx];
                    }
                });
                if (side) row.side = side;
                return row;
            });
    };
    const normalize = (raw) => {
        if (!raw) return [];
        const rows = [];
        const pushRows = (obj, side) => {
            if (!obj) return;
            if (Array.isArray(obj)) {
                obj.forEach(r => rows.push(side ? { ...r, side } : r));
            } else {
                rows.push(...toRowsFromColumns(obj, side));
            }
        };
        if (raw.calls || raw.puts) {
            pushRows(raw.calls, 'Call');
            pushRows(raw.puts, 'Put');
        } else {
            pushRows(raw, null);
        }
        return rows;
    };
    const pick = (row, keys) => {
        for (const key of keys) {
            if (row[key] !== undefined && row[key] !== null) return row[key];
        }
        return null;
    };
    const formatNum = (val, decimals = 2) => (val === null || val === undefined || isNaN(val) ? '—' : Number(val).toFixed(decimals));
    const formatPct = (val) => (val === null || val === undefined || isNaN(val) ? '—' : `${Number(val).toFixed(2)}%`);
    const formatInt = (val) => (val === null || val === undefined || isNaN(val) ? '—' : Number(val).toLocaleString());
    const formatIV = (val) => {
        if (val === null || val === undefined || isNaN(val)) return '—';
        const num = Number(val);
        return num > 5 ? `${num.toFixed(2)}` : `${(num * 100).toFixed(1)}%`;
    };
    const formatDate = (val) => {
        if (!val) return '—';
        const d = new Date(val);
        return isNaN(d.getTime()) ? val : d.toLocaleDateString();
    };
    const formatBool = (val) => {
        if (val === true || val === 1) return 'Yes';
        if (val === false || val === 0) return 'No';
        return '—';
    };
    const rows = normalize(data)
        .map(r => ({
            side: pick(r, ['side']),
            contract: pick(r, ['contractSymbol', 'symbol']),
            strike: pick(r, ['strike', 'Strike']),
            last: pick(r, ['lastPrice', 'LastPrice', 'last']),
            bid: pick(r, ['bid', 'Bid']),
            ask: pick(r, ['ask', 'Ask']),
            change: pick(r, ['change', 'Change']),
            percentChange: pick(r, ['percentChange', 'PercentChange']),
            volume: pick(r, ['volume', 'Volume']),
            openInterest: pick(r, ['openInterest', 'OpenInterest']),
            impliedVol: pick(r, ['impliedVolatility', 'ImpliedVolatility', 'impliedVol']),
            inTheMoney: pick(r, ['inTheMoney', 'inTheMoneyFlag', 'ITM']),
            lastTrade: pick(r, ['lastTradeDate', 'lastTrade', 'lastTradeDateTime'])
        }))
        .filter(r => r.contract || r.strike !== undefined)
        .sort((a, b) => (Number(a.strike) || 0) - (Number(b.strike) || 0))
        .slice(0, 30);
    if (!rows.length) {
        hideCardIfEmpty(container);
        return;
    }
    const tableRows = rows.map(r => {
        const itm = formatBool(r.inTheMoney);
        const itmClass = itm === 'Yes' ? ' style="background: rgba(34,197,94,0.08);"' : '';
        return `
            <tr${itmClass}>
                <td>${escapeHtml(r.side || 'Call')}</td>
                <td>${escapeHtml(r.contract || '—')}</td>
                <td>${formatNum(r.strike)}</td>
                <td>${formatNum(r.last)}</td>
                <td>${formatNum(r.bid)}</td>
                <td>${formatNum(r.ask)}</td>
                <td>${formatNum(r.change)}</td>
                <td>${formatPct(r.percentChange)}</td>
                <td>${formatInt(r.volume)}</td>
                <td>${formatInt(r.openInterest)}</td>
                <td>${formatIV(r.impliedVol)}</td>
                <td>${itm}</td>
                <td>${escapeHtml(formatDate(r.lastTrade))}</td>
            </tr>
        `;
    }).join('');
    container.innerHTML = `
        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 12px; color: var(--text-secondary, #555);">
            <div>First expiration shown • Sorted by strike • Top ${rows.length} rows</div>
            <div>ITM rows highlighted</div>
        </div>
        <div style="overflow-x: auto; max-height: 340px; border: 1px solid #e5e7eb; border-radius: 4px; box-shadow: inset 0 1px 0 rgba(0,0,0,0.02);">
            <table style="min-width: 760px;">
                <thead>
                    <tr>
                        <th>Side</th>
                        <th>Contract</th>
                        <th>Strike</th>
                        <th>Last</th>
                        <th>Bid</th>
                        <th>Ask</th>
                        <th>Change</th>
                        <th>% Chg</th>
                        <th>Vol</th>
                        <th>OI</th>
                        <th>IV</th>
                        <th>ITM</th>
                        <th>Last Trade</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function renderAIRecommendation(data, container) {
    const text = typeof data === 'string' ? data : JSON.stringify(data);
    
    // Determine recommendation type
    let className = '';
    const upperText = text.toUpperCase();
    if (upperText.includes('BUY') && !upperText.includes('NOT BUY')) {
        className = 'buy';
    } else if (upperText.includes('SELL')) {
        className = 'sell';
    } else if (upperText.includes('HOLD')) {
        className = 'hold';
    }
    
    container.innerHTML = `<div class="recommendation-box ${className}">${escapeHtml(text)}</div>`;
}

function renderTechnicalAnalysis(data, container) {
    const text = typeof data === 'string' ? data : JSON.stringify(data);
    container.innerHTML = `<div style="white-space: pre-wrap; line-height: 1.8;">${escapeHtml(text)}</div>`;
}

function renderNewsSentiment(data, container) {
    const text = typeof data === 'string' ? data : JSON.stringify(data);
    container.innerHTML = `<div style="white-space: pre-wrap; line-height: 1.8;">${escapeHtml(text)}</div>`;
}

function renderTechnicalSignals(_data, container) {
    const ind = window.technicalIndicators || {};
    if (!ind || (!ind.rsi && !ind.macd && !ind.stochastic)) {
        container.innerHTML = '<p class="text-muted">Load price history to see signals</p>';
        return;
    }
    const rsiSignal = ind.rsi > 70 ? 'Overbought' : ind.rsi < 30 ? 'Oversold' : 'Neutral';
    const macdSignal = ind.macdHistogram && ind.macdHistogram !== null ? (ind.macdHistogram > 0 ? 'Bullish' : 'Bearish') : 'Neutral';
    const stochSignal = ind.stochastic > 80 ? 'Overbought' : ind.stochastic < 20 ? 'Oversold' : 'Neutral';
    const adxSignal = ind.adx && ind.adx > 25 ? 'Trending' : 'Weak Trend';
    const smaSignal = (window.currentPrice || 0) > (ind.sma20 || 0) && (ind.sma20 || 0) > (ind.sma50 || 0) ? 'Bullish' : (window.currentPrice || 0) < (ind.sma20 || 0) && (ind.sma20 || 0) < (ind.sma50 || 0) ? 'Bearish' : 'Mixed';
    
    const row = (label, value, signal) => `
        <tr>
            <td>${label}</td>
            <td class="value">${value}</td>
            <td class="value">${signal}</td>
        </tr>
    `;
    
    const html = `
        <table>
            ${row('RSI (14)', ind.rsi ? ind.rsi.toFixed(1) : 'N/A', rsiSignal)}
            ${row('MACD', ind.macd ? ind.macd.toFixed(3) : 'N/A', macdSignal)}
            ${row('MACD Hist', ind.macdHistogram ? ind.macdHistogram.toFixed(3) : 'N/A', macdSignal)}
            ${row('Stochastic', ind.stochastic ? ind.stochastic.toFixed(1) : 'N/A', stochSignal)}
            ${row('ADX', ind.adx ? ind.adx.toFixed(1) : 'N/A', adxSignal)}
            ${row('SMA 20', ind.sma20 ? formatCurrency(ind.sma20) : 'N/A', smaSignal)}
            ${row('SMA 50', ind.sma50 ? formatCurrency(ind.sma50) : 'N/A', smaSignal)}
            ${row('BB Upper', ind.bbUpper ? formatCurrency(ind.bbUpper) : 'N/A', '-')}
            ${row('BB Lower', ind.bbLower ? formatCurrency(ind.bbLower) : 'N/A', '-')}
        </table>
    `;
    container.innerHTML = html;
}

// Utility functions
function renderTable(fields, container) {
    const rows = Object.entries(fields)
        .filter(([_, value]) => value !== null && value !== undefined && value !== 'N/A')
        .map(([key, value]) => `
            <tr>
                <td>${key}</td>
                <td class="value">${value}</td>
            </tr>
        `).join('');
    
    if (rows) {
        container.innerHTML = `<table>${rows}</table>`;
    } else {
        hideCardIfEmpty(container);
    }
}

function formatCurrency(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    return '$' + Number(value).toFixed(2);
}

function formatNumber(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    return Number(value).toFixed(2);
}

function formatPercent(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    return (Number(value) * 100).toFixed(2) + '%';
}

function formatLargeNumber(value) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    const num = Number(value);
    if (num >= 1e12) return '$' + (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return '$' + (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return '$' + (num / 1e6).toFixed(2) + 'M';
    return '$' + num.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load AI Selected BUYs on landing page
async function loadAIBuys() {
    const container = document.getElementById('ai-buys-container');
    if (!container) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/screen-undervalued`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        let stocks = [];
        if (Array.isArray(data)) {
            stocks = data;
        } else if (data.stocks && Array.isArray(data.stocks)) {
            stocks = data.stocks;
        } else if (data.data && Array.isArray(data.data)) {
            stocks = data.data;
        } else if (typeof data === 'object' && data !== null) {
            stocks = Object.keys(data).slice(0, 10);
        }
        
        if (!stocks || stocks.length === 0) {
            container.innerHTML = '<div style="color: var(--text-secondary); font-size: 13px;">No recommendations available</div>';
            return;
        }
        
        const tickers = stocks.slice(0, 10).map(item => {
            if (typeof item === 'string') return item.toUpperCase();
            if (item.ticker) return item.ticker.toUpperCase();
            if (item.symbol) return item.symbol.toUpperCase();
            return null;
        }).filter(Boolean);
        
        container.innerHTML = tickers.map(ticker => `
            <div class="ai-buy-ticker" onclick="handleTickerClick('${escapeHtml(ticker)}')" title="Analyze ${escapeHtml(ticker)}">
                <span class="ticker-symbol">${escapeHtml(ticker)}</span>
                <span class="ticker-price" id="price-${escapeHtml(ticker)}">...</span>
            </div>
        `).join('');
        
        // Fetch prices for each ticker
        tickers.forEach(async (ticker) => {
            try {
                const priceResponse = await fetch(`${API_BASE_URL}/api/fundamentals/${ticker}`);
                if (priceResponse.ok) {
                    const priceData = await priceResponse.json();
                    const price = priceData.currentPrice || priceData.current_price || priceData.regularMarketPrice;
                    const priceEl = document.getElementById(`price-${ticker}`);
                    if (priceEl && price) {
                        priceEl.textContent = formatCurrency(price);
                    } else if (priceEl) {
                        priceEl.textContent = '';
                    }
                }
            } catch (err) {
                const priceEl = document.getElementById(`price-${ticker}`);
                if (priceEl) priceEl.textContent = '';
            }
        });
    } catch (error) {
        console.error('Error loading AI buys:', error);
        container.innerHTML = '<div style="color: var(--text-secondary); font-size: 13px;">Unable to load recommendations</div>';
    }
}

// Handle clicking a ticker in AI Buys section
function handleTickerClick(ticker) {
    if (!ticker) return;
    hideError();
    currentTicker = ticker;
    tickerInput.value = ticker;
    loadStockData(ticker);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    tickerInput.focus();
    loadAIBuys();
});
