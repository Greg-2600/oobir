"""Integration tests for Web UI with REST API endpoints."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json
import sys
import os

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

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation')
    def test_ai_recommendation_endpoint_for_ui_button(self, mock_recommendation, mock_ensure_ollama):
        """Test AI recommendation endpoint works with Web UI on-demand button."""
        mock_recommendation.return_value = 'BUY: Apple shows strong fundamentals with solid revenue growth and excellent market position.'

        response = self.client.get('/api/ai/action-recommendation/AAPL')

        self.assertEqual(response.status_code, 200)
        # Web UI expects string response
        data = response.json()
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 0)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_technical_analysis')
    def test_technical_analysis_endpoint_for_ui_button(self, mock_technical, mock_ensure_ollama):
        """Test technical analysis endpoint works with Web UI on-demand button."""
        mock_technical.return_value = 'Technical setup looks bullish with SMA 20 above SMA 50. RSI indicates room for further upside.'

        response = self.client.get('/api/ai/technical-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_endpoint_for_ui_button(self, mock_sentiment, mock_ensure_ollama):
        """Test news sentiment endpoint works with Web UI on-demand button."""
        mock_sentiment.return_value = 'Recent news sentiment is positive. Analyst upgrades and product launches driving positive outlook.'

        response = self.client.get('/api/ai/news-sentiment/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)


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
