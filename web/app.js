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

// Handle search submission
function handleSearch(e) {
    e.preventDefault();
    const ticker = (e.target === searchForm ? tickerInput : tickerInputCompact).value.trim().toUpperCase();
    
    if (!ticker) {
        showError('Please enter a stock ticker');
        return;
    }
    
    if (!/^[A-Z]{1,5}$/.test(ticker)) {
        showError('Please enter a valid stock ticker (1-5 letters)');
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
    
    // Initialize AI recommendation with a button
    initializeAIRecommendation(ticker);
    
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

// Render functions
function renderFundamentals(data, container) {
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
    if (!data || !data.data || !Array.isArray(data.data)) {
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
    
    // Create simple chart
    const chartHtml = `
        <div class="price-chart">
            ${prices.map(day => {
                const height = ((day.Close - Math.min(...prices.map(p => p.Close))) / 
                              (Math.max(...prices.map(p => p.Close)) - Math.min(...prices.map(p => p.Close)))) * 100;
                return `<div class="price-bar" style="height: ${height}%" title="${day.Date}: $${day.Close.toFixed(2)}"></div>`;
            }).join('')}
        </div>
        <div style="text-align: center; margin-top: 16px;">
            <strong>Latest Close:</strong> ${formatCurrency(latest.Close)} | 
            <strong>High:</strong> ${formatCurrency(Math.max(...prices.map(p => p.High)))} | 
            <strong>Low:</strong> ${formatCurrency(Math.min(...prices.map(p => p.Low)))}
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
        'Current Price': formatCurrency(data.currentPrice || data.current_price),
        'Target High': formatCurrency(data.targetHighPrice || data.target_high_price),
        'Target Mean': formatCurrency(data.targetMeanPrice || data.target_mean_price),
        'Target Low': formatCurrency(data.targetLowPrice || data.target_low_price),
        'Recommendation': (data.recommendationKey || data.recommendation_key || 'N/A').toUpperCase(),
        'Number of Analysts': data.numberOfAnalystOpinions || data.number_of_analyst_opinions || 'N/A'
    };
    
    renderTable(fields, container);
}

function renderCalendar(data, container) {
    if (!data || !Array.isArray(data) || data.length === 0) {
        container.innerHTML = '<p class="text-muted">No upcoming events</p>';
        return;
    }
    
    const html = data.map(event => `
        <div class="news-item">
            <div class="news-title">${event.event || event.title || 'Event'}</div>
            <div class="news-meta">${event.date || event.eventDate || 'Date TBD'}</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function renderIncomeStatement(data, container) {
    if (!data || typeof data !== 'object') {
        container.innerHTML = '<p class="text-muted">No income statement available</p>';
        return;
    }
    
    const fields = {
        'Revenue': formatLargeNumber(data.totalRevenue || data.total_revenue),
        'Gross Profit': formatLargeNumber(data.grossProfit || data.gross_profit),
        'Operating Income': formatLargeNumber(data.operatingIncome || data.operating_income),
        'Net Income': formatLargeNumber(data.netIncome || data.net_income),
        'EPS': formatNumber(data.basicEPS || data.basic_eps),
        'EBITDA': formatLargeNumber(data.ebitda)
    };
    
    renderTable(fields, container);
}

function renderBalanceSheet(data, container) {
    if (!data || typeof data !== 'object') {
        container.innerHTML = '<p class="text-muted">No balance sheet available</p>';
        return;
    }
    
    const fields = {
        'Total Assets': formatLargeNumber(data.totalAssets || data.total_assets),
        'Total Liabilities': formatLargeNumber(data.totalLiabilitiesNetMinorityInterest || data.total_liabilities),
        'Cash': formatLargeNumber(data.cashAndCashEquivalents || data.cash),
        'Total Debt': formatLargeNumber(data.totalDebt || data.total_debt),
        'Stockholders Equity': formatLargeNumber(data.stockholdersEquity || data.stockholders_equity)
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
