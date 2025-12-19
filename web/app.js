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
        balanceSheet: fetchData(`/api/balance-sheet/${ticker}`, 'balance-sheet-data', renderBalanceSheet)
    };
    
    // Wait for all data to load
    await Promise.allSettled(Object.values(dataPromises));
    
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
        console.log(`Fetched ${endpoint}:`, data); // Debug logging
        renderFunction(data, container);
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        container.innerHTML = `<p class="text-danger">❌ Failed to load data</p>`;
    }
}

// Render functions
function renderFundamentals(data, container) {
    console.log('renderFundamentals called with:', data);
    if (!data || typeof data !== 'object') {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
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
    
    // Calculate technical indicators
    const sma20 = calculateSMA(prices, 20);
    const sma50 = calculateSMA(prices, 50);
    const { upper: bbUpper, lower: bbLower } = calculateBollingerBands(prices, 20, 2);
    
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
            <div style="display: flex; align-items: flex-end; justify-content: space-around; gap: 2px; height: 280px; padding: 10px; background: #f9f9f9; border-radius: 4px; position: relative;">
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
            
            <!-- Stats -->
            <div style="text-align: center; margin-top: 16px; font-size: 0.9em; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                <div><strong>Latest Close:</strong> ${formatCurrency(latest.Close)}</div>
                <div><strong>High:</strong> ${formatCurrency(maxPrice)}</div>
                <div><strong>Low:</strong> ${formatCurrency(minPrice)}</div>
                <div><strong>SMA 20:</strong> ${formatCurrency(sma20[sma20.length - 1] || 0)}</div>
                <div><strong>SMA 50:</strong> ${formatCurrency(sma50[sma50.length - 1] || 0)}</div>
            </div>
        </div>
    `;
    
    container.innerHTML = chartHtml;
}

function renderAnalystTargets(data, container) {
    if (!data || typeof data !== 'object') {
        container.innerHTML = '<p class="text-muted">No analyst data available</p>';
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
        container.innerHTML = '<p class="text-muted">No upcoming events</p>';
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
        container.innerHTML = '<p class="text-muted">No income statement available</p>';
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
        container.innerHTML = '<p class="text-muted">No balance sheet available</p>';
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
        container.innerHTML = '<p class="text-muted">No data available</p>';
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    tickerInput.focus();
});
