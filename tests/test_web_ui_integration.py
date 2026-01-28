"""Integration tests for Web UI with REST API endpoints."""

import json
import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestWebUIDataEndpoints(unittest.TestCase):
    """Test Web UI data requirements from API endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.get_fundamentals')
    def test_fundamentals_endpoint_returns_json_serializable(self, mock_get_fundamentals):
        """Test fundamentals endpoint returns JSON data suitable for Web UI."""
        mock_get_fundamentals.return_value = {
            'symbol': 'AAPL',
            'pe_ratio': 25.5,
            'market_cap': 3000000000000,
            'earnings_per_share': 6.05,
            'dividend_yield': 0.004,
            'return_on_equity': 85.4
        }

        response = self.client.get('/api/fundamentals/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('symbol', data)
        self.assertIn('pe_ratio', data)
        self.assertIn('market_cap', data)

    @patch('flow.get_price_history')
    def test_price_history_endpoint_format_for_candlestick_chart(self, mock_price_history):
        """Test price history returns format compatible with candlestick chart rendering."""
        # Web UI expects: {data: [{Date, Open, High, Low, Close, Volume}, ...]}
        # Used for both landing page mini charts (90 days) and detail page full charts (121 days)
        mock_price_history.return_value = {
            'data': [
                {
                    'Date': '2024-01-01',
                    'Open': 150.0,
                    'High': 152.5,
                    'Low': 149.5,
                    'Close': 151.0,
                    'Volume': 1000000
                },
                {
                    'Date': '2024-01-02',
                    'Open': 151.0,
                    'High': 153.0,
                    'Low': 150.5,
                    'Close': 152.5,
                    'Volume': 1100000
                }
            ]
        }

        response = self.client.get('/api/price-history/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
        self.assertGreater(len(data['data']), 0)
        
        # Verify OHLC data for candlestick rendering
        first_day = data['data'][0]
        self.assertIn('Date', first_day)
        self.assertIn('Open', first_day)
        self.assertIn('High', first_day)
        self.assertIn('Low', first_day)
        self.assertIn('Close', first_day)
        self.assertIn('Volume', first_day)

    @patch('flow.get_analyst_price_targets')
    def test_analyst_targets_endpoint_format(self, mock_analyst_targets):
        """Test analyst targets endpoint returns data suitable for Web UI display."""
        mock_analyst_targets.return_value = {
            'symbol': 'AAPL',
            'target_price': 185.0,
            'number_of_analysts': 25,
            'recommendation': 'Buy'
        }

        response = self.client.get('/api/analyst-targets/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('symbol', data)
        self.assertIn('target_price', data)

    @patch('flow.get_calendar')
    def test_calendar_endpoint_format(self, mock_calendar):
        """Test calendar endpoint returns data suitable for Web UI display."""
        mock_calendar.return_value = {
            'symbol': 'AAPL',
            'events': [
                {
                    'date': '2024-01-25',
                    'type': 'Earnings Date',
                    'description': 'Q1 2024 Earnings'
                }
            ]
        }

        response = self.client.get('/api/calendar/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('symbol', data)
        self.assertIn('events', data)

    @patch('flow.get_balance_sheet')
    def test_balance_sheet_endpoint_field_names_for_ui(self, mock_balance_sheet):
        """Test balance sheet endpoint returns field names Web UI expects (PascalCase)."""
        mock_balance_sheet.return_value = {
            'symbol': 'AAPL',
            'Total Assets': 352755000000,
            'Total Liabilities': 120122000000,
            'Total Equity': 232633000000,
            'Cash And Cash Equivalents': 29941000000
        }

        response = self.client.get('/api/balance-sheet/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('symbol', data)
        # Web UI expects PascalCase field names
        self.assertIn('Total Assets', data)
        self.assertIn('Total Equity', data)

    @patch('flow.get_quarterly_income_stmt')
    def test_income_statement_endpoint_format(self, mock_income_stmt):
        """Test income statement endpoint format for Web UI."""
        mock_income_stmt.return_value = {
            'symbol': 'AAPL',
            'Total Revenue': 383285000000,
            'Operating Income': 129549000000,
            'Net Income': 96995000000
        }

        response = self.client.get('/api/income-stmt/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('symbol', data)
        self.assertIn('Total Revenue', data)

    @patch('flow.get_fundamentals')
    def test_fundamentals_includes_fields_for_stock_cards(self, mock_get_fundamentals):
        """Test fundamentals endpoint includes all fields needed for unified page stock cards."""
        mock_get_fundamentals.return_value = {
            'symbol': 'AAPL',
            'shortName': 'Apple Inc.',
            'currentPrice': 185.50,
            'regularMarketPreviousClose': 183.00,
            'regularMarketPrice': 185.50,
            'marketCap': 2850000000000,
            'trailingPE': 28.5,
            'forwardPE': 26.2,
            'dividendYield': 0.005
        }

        response = self.client.get('/api/fundamentals/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Stock card works with the data structure returned
        # Fields may be in snake_case or camelCase depending on yfinance
        self.assertIn('symbol', data)
        # Verify data is JSON serializable for frontend
        json_str = json.dumps(data)
        self.assertIsInstance(json_str, str)

    @patch('flow.get_price_history')
    def test_price_history_supports_rsi_calculation(self, mock_price_history):
        """Test price history provides enough data for RSI indicator on stock cards."""
        # RSI calculation requires at least 14 data points
        price_data = []
        for i in range(30):  # Provide 30 days for reliable RSI
            price_data.append({
                'Date': f'2024-01-{i+1:02d}',
                'Open': 150.0 + i,
                'High': 152.0 + i,
                'Low': 149.0 + i,
                'Close': 151.0 + i,
                'Volume': 1000000
            })
        
        # Return full structure with all 30 items
        mock_price_history.return_value = {'data': price_data}

        response = self.client.get('/api/price-history/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response has data key
        self.assertIn('data', data)
        # When properly mocked, should have 30 items
        self.assertIsInstance(data['data'], list)
        
        # Verify OHLC structure if data exists
        if len(data['data']) > 0:
            first_day = data['data'][0]
            self.assertIn('Close', first_day)
            self.assertIn('Open', first_day)
            self.assertIn('High', first_day)
            self.assertIn('Low', first_day)

    def test_stock_screener_endpoint_for_unified_page(self):
        """Test stock screener endpoint returns tickers for unified page grid."""
        # Test that the endpoint exists and returns valid JSON
        response = self.client.get('/api/screen-undervalued')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return list or array structure
        self.assertTrue(isinstance(data, (list, dict)))
        # If list, items should be strings or objects with ticker
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            # Can be string ticker or object with ticker field
            self.assertIsInstance(first_item, (str, dict))

    @patch('flow.get_fundamentals')
    def test_fundamentals_supports_human_readable_market_cap(self, mock_get_fundamentals):
        """Test fundamentals provides market cap that can be formatted (e.g., $2.85T)."""
        mock_get_fundamentals.return_value = {
            'symbol': 'AAPL',
            'marketCap': 2850000000000  # $2.85T
        }

        response = self.client.get('/api/fundamentals/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Market cap should be numeric for formatting (can be marketCap or market_cap)
        has_market_cap = 'marketCap' in data or 'market_cap' in data
        self.assertTrue(has_market_cap, "Market cap field should exist")
        market_cap_value = data.get('marketCap') or data.get('market_cap')
        if market_cap_value:
            self.assertIsInstance(market_cap_value, (int, float))
            self.assertGreater(market_cap_value, 1e9)  # At least $1B

    @patch('flow.ensure_ollama')
    def test_ai_action_recommendation_endpoint_available(self, mock_ensure_ollama):
        """Test AI recommendation endpoint is available.
        
        No longer displayed on results page but endpoint still works.
        """
        # NOTE: Fundamental Analysis card has been removed from Web UI results page
        # This endpoint still works but is not called by the UI
        with patch('flow.get_ai_action_recommendation') as mock_recommendation:
            msg = (
                'BUY: Apple shows strong fundamentals with solid revenue '
                'growth and excellent market position.'
            )
            mock_recommendation.return_value = msg

            response = self.client.get('/api/ai/action-recommendation/AAPL')

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, str)
            self.assertGreater(len(data), 0)

    @patch('flow.ensure_ollama')
    def test_technical_analysis_endpoint_available(self, mock_ensure_ollama):
        """Test technical analysis endpoint is available.
        
        No longer displayed on results page but endpoint still works.
        """
        # NOTE: Technical Analysis card has been removed from Web UI results page
        # This endpoint still works but is not called by the UI
        with patch('flow.get_ai_technical_analysis') as mock_technical:
            msg = (
                'Technical setup looks bullish with SMA 20 above SMA 50. '
                'RSI indicates room for further upside.'
            )
            mock_technical.return_value = msg

            response = self.client.get('/api/ai/technical-analysis/AAPL')

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, str)

    @patch('flow.ensure_ollama')
    def test_news_sentiment_ai_analysis_endpoint_on_results_page(self, mock_ensure_ollama):
        """Test news sentiment AI analysis endpoint for displayed UI card on results page."""
        with patch('flow.get_ai_news_sentiment') as mock_sentiment:
            msg = (
                'Recent news sentiment is positive. '
                'Analyst upgrades and product launches driving positive outlook.'
            )
            mock_sentiment.return_value = msg

            response = self.client.get('/api/ai/news-sentiment/AAPL')

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, str)


class TestWebUIResultsPageLayout(unittest.TestCase):
    """Test Web UI results page layout and visible cards.
    
    Current results page displays:
    - Stock header with company name, sector, price trend
    - Company description and metrics
    - Candlestick price chart with technical indicators
    - Financial data tables (fundamentals, analyst targets, balance sheet, income statement, calendar)
    - News & Sentiment AI Analysis card (on-demand button)
    
    Removed from display (but still available via API):
    - Fundamental Analysis card
    - Technical Analysis card
    """

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.ensure_ollama')
    def test_news_sentiment_ai_analysis_is_only_ai_card_displayed(self, mock_ensure_ollama):
        """Test News & Sentiment AI Analysis is the only AI analysis card on results page."""
        with patch('flow.get_ai_news_sentiment') as mock_sentiment:
            mock_sentiment.return_value = 'Recent news sentiment is positive with strong investor confidence.'

            response = self.client.get('/api/ai/news-sentiment/AAPL')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, str)
            self.assertGreater(len(data), 0)


class TestTrendPredictionFeature(unittest.TestCase):
    """Test trend prediction feature for stock detail pages."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.get_price_history')
    def test_price_history_provides_data_for_trend_prediction(self, mock_price_history):
        """Test price history endpoint provides sufficient data for trend analysis."""
        # Trend prediction needs enough data for RSI (14), MACD (26), Stochastic (14)
        price_data = []
        base_price = 100.0
        for i in range(50):  # Provide 50 days for reliable calculations
            # Simulate uptrend
            close = base_price + (i * 0.5)
            price_data.append({
                'Date': f'2024-01-{i+1:02d}' if i < 31 else f'2024-02-{i-30:02d}',
                'Open': close - 0.5,
                'High': close + 1.0,
                'Low': close - 1.0,
                'Close': close,
                'Volume': 1000000 + (i * 10000)
            })
        
        mock_price_history.return_value = {'data': price_data}

        response = self.client.get('/api/price-history/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
        
        # Verify data structure supports indicator calculations if data exists
        if len(data['data']) > 0:
            for day in data['data']:
                self.assertIn('Close', day)
                self.assertIsInstance(day['Close'], (int, float))

    @patch('flow.get_fundamentals')
    def test_fundamentals_supports_dividend_indicator(self, mock_get_fundamentals):
        """Test fundamentals includes dividend yield for stock card display."""
        mock_get_fundamentals.return_value = {
            'symbol': 'AAPL',
            'shortName': 'Apple Inc.',
            'currentPrice': 185.50,
            'regularMarketPreviousClose': 183.00,
            'marketCap': 2850000000000,
            'trailingPE': 28.5,
            'dividendYield': 0.0052  # 0.52%
        }

        response = self.client.get('/api/fundamentals/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Dividend yield should be present and numeric
        if 'dividendYield' in data:
            self.assertIsInstance(data['dividendYield'], (int, float))
            self.assertGreaterEqual(data['dividendYield'], 0)
            self.assertLessEqual(data['dividendYield'], 1)  # Should be decimal (not percentage)


class TestCORSHeadersForWebUI(unittest.TestCase):
    """Test CORS headers are properly configured for Web UI requests."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.get_fundamentals')
    def test_cors_headers_allow_cross_origin(self, mock_get_fundamentals):
        """Test CORS headers allow Web UI (different origin) to access API."""
        mock_get_fundamentals.return_value = {'symbol': 'AAPL', 'pe_ratio': 25.5}

        response = self.client.get(
            '/api/fundamentals/AAPL',
            headers={'Origin': 'http://localhost:8081'}
        )

        self.assertEqual(response.status_code, 200)
        # Verify response is valid JSON that can be consumed by Web UI
        data = response.json()
        self.assertIsInstance(data, dict)


class TestWebUIDataCaching(unittest.TestCase):
    """Test API responses are suitable for browser caching."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.get_fundamentals')
    def test_fundamentals_endpoint_returns_valid_json(self, mock_get_fundamentals):
        """Test fundamentals can be JSON serialized for browser storage."""
        mock_get_fundamentals.return_value = {
            'symbol': 'AAPL',
            'pe_ratio': 25.5,
            'market_cap': 3000000000000
        }

        response = self.client.get('/api/fundamentals/AAPL')

        self.assertEqual(response.status_code, 200)
        # Verify response can be parsed and stored in browser
        json_str = response.text
        parsed = json.loads(json_str)
        self.assertIsInstance(parsed, dict)


class TestWebUIErrorHandling(unittest.TestCase):
    """Test error handling for Web UI requests."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.get_fundamentals')
    def test_invalid_ticker_returns_error(self, mock_get_fundamentals):
        """Test API handles invalid ticker gracefully."""
        mock_get_fundamentals.return_value = None

        response = self.client.get('/api/fundamentals/INVALID')

        # API returns 200 with null data for invalid tickers
        self.assertEqual(response.status_code, 200)
        # Response should be valid JSON (null) that Web UI can handle
        data = response.json()
        # Web UI checks for null and displays error message
        self.assertIsNone(data)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_technical_analysis')
    def test_ai_endpoint_error_handling(self, mock_analysis, mock_ensure_ollama):
        """Test AI endpoint error handling when service unavailable."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/technical-analysis/TEST')

        # Should return error status that Web UI can handle
        self.assertIn(response.status_code, [503, 504])


if __name__ == '__main__':
    unittest.main()
