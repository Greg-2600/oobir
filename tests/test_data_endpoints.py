"""Unit tests for data endpoints."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestDataEndpoints(unittest.TestCase):
    """Test cases for data retrieval endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())

    @patch('requests.get')
    def test_ollama_health_endpoint(self, mock_requests_get):
        """Test Ollama health check endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        response = self.client.get('/health/ollama')

        self.assertEqual(response.status_code, 200)

    @patch('flow.get_fundamentals')
    def test_fundamentals_endpoint(self, mock_get_fundamentals):
        """Test fundamentals endpoint."""
        mock_get_fundamentals.return_value = {
            'symbol': 'AAPL',
            'pe_ratio': 25.5,
            'market_cap': 3000000000000
        }

        response = self.client.get('/api/fundamentals/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['symbol'], 'AAPL')

    @patch('flow.get_fundamentals')
    def test_fundamentals_endpoint_error(self, mock_get_fundamentals):
        """Test fundamentals endpoint error handling."""
        mock_get_fundamentals.side_effect = Exception('API Error')

        response = self.client.get('/api/fundamentals/INVALID')

        self.assertEqual(response.status_code, 500)

    @patch('flow.get_price_history')
    def test_price_history_endpoint(self, mock_get_price_history):
        """Test price history endpoint."""
        mock_get_price_history.return_value = [
            {'date': '2024-01-01', 'close': 150.0},
            {'date': '2024-01-02', 'close': 152.0}
        ]

        response = self.client.get('/api/price-history/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    @patch('flow.get_analyst_price_targets')
    def test_analyst_targets_endpoint(self, mock_get_analyst_targets):
        """Test analyst targets endpoint."""
        mock_get_analyst_targets.return_value = {
            'symbol': 'AAPL',
            'target_high': 200.0,
            'target_low': 150.0,
            'target_mean': 175.0
        }

        response = self.client.get('/api/analyst-targets/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['symbol'], 'AAPL')

    @patch('flow.get_calendar')
    def test_calendar_endpoint(self, mock_get_calendar):
        """Test calendar endpoint."""
        mock_get_calendar.return_value = [
            {'event': 'Earnings', 'date': '2024-01-25'}
        ]

        response = self.client.get('/api/calendar/AAPL')

        self.assertEqual(response.status_code, 200)

    @patch('flow.get_quarterly_income_stmt')
    def test_income_stmt_endpoint(self, mock_get_income_statement):
        """Test income statement endpoint."""
        mock_get_income_statement.return_value = {
            'symbol': 'AAPL',
            'revenue': 383285000000,
            'net_income': 96995000000
        }

        response = self.client.get('/api/income-stmt/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['symbol'], 'AAPL')

    @patch('flow.get_balance_sheet')
    def test_balance_sheet_endpoint(self, mock_get_balance_sheet):
        """Test balance sheet endpoint."""
        mock_get_balance_sheet.return_value = {
            'symbol': 'AAPL',
            'total_assets': 352755000000,
            'total_liabilities': 120715000000
        }

        response = self.client.get('/api/balance-sheet/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['symbol'], 'AAPL')

    @patch('flow.get_option_chain')
    def test_option_chain_endpoint(self, mock_get_option_chain):
        """Test option chain endpoint."""
        mock_get_option_chain.return_value = {
            'symbol': 'AAPL',
            'calls': [],
            'puts': []
        }

        response = self.client.get('/api/option-chain/AAPL')

        self.assertEqual(response.status_code, 200)

    @patch('flow.get_news')
    def test_news_endpoint(self, mock_get_news):
        """Test news endpoint."""
        mock_get_news.return_value = [
            {
                'title': 'Apple News',
                'source': 'Reuters',
                'published': '2024-01-01T10:00:00Z'
            }
        ]

        response = self.client.get('/api/news/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    @patch('flow.get_screen_undervalued_large_caps')
    def test_screen_undervalued_endpoint(self, mock_screen_undervalued):
        """Test screen undervalued endpoint."""
        mock_screen_undervalued.return_value = ['AAPL', 'MSFT', 'GOOGL']

        response = self.client.get('/api/screen-undervalued')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    @patch('flow.get_screen_undervalued_large_caps')
    def test_screen_undervalued_endpoint_error(self, mock_screen_undervalued):
        """Test screen undervalued endpoint error handling."""
        mock_screen_undervalued.side_effect = Exception('Screening failed')

        response = self.client.get('/api/screen-undervalued')

        self.assertEqual(response.status_code, 500)


if __name__ == '__main__':
    unittest.main()
