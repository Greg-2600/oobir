"""Unit tests for news sentiment API endpoint."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestNewsSentimentAPI(unittest.TestCase):
    """Test cases for the /api/ai/news-sentiment/{symbol} endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_endpoint_success(self, mock_get_sentiment, mock_ensure_ollama):
        """Test successful news sentiment endpoint call."""
        mock_get_sentiment.return_value = 'Positive sentiment for investors.'

        response = self.client.get('/api/ai/news-sentiment/AAPL')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Positive', response.json())

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_endpoint_none_result(self, mock_get_sentiment, mock_ensure_ollama):
        """Test news sentiment endpoint when function returns None."""
        mock_get_sentiment.return_value = None

        response = self.client.get('/api/ai/news-sentiment/TEST')

        self.assertEqual(response.status_code, 503)
        self.assertIn('unavailable', response.json()['detail'].lower())

    @patch('flow.ensure_ollama')
    def test_news_sentiment_endpoint_ollama_error(self, mock_ensure_ollama):
        """Test news sentiment endpoint when Ollama connection fails."""
        mock_ensure_ollama.side_effect = Exception('Connection failed')

        response = self.client.get('/api/ai/news-sentiment/TEST')

        self.assertEqual(response.status_code, 500)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_endpoint_various_symbols(self, mock_get_sentiment, mock_ensure_ollama):
        """Test news sentiment endpoint with various stock symbols."""
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'CHTR']
        
        for symbol in test_symbols:
            mock_get_sentiment.return_value = f'Sentiment for {symbol}.'
            
            response = self.client.get(f'/api/ai/news-sentiment/{symbol}')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn(symbol, response.json())

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_response_format(self, mock_get_sentiment, mock_ensure_ollama):
        """Test that news sentiment response has correct format."""
        sentiment_text = 'The recent news indicates moderate optimism with some concerns about market conditions.'
        mock_get_sentiment.return_value = sentiment_text

        response = self.client.get('/api/ai/news-sentiment/TSLA')

        self.assertEqual(response.status_code, 200)
        result = response.json()
        # Response should be a string
        self.assertIsInstance(result, str)
        self.assertEqual(result, sentiment_text)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_case_insensitive(self, mock_get_sentiment, mock_ensure_ollama):
        """Test that symbol parameter is passed correctly regardless of case."""
        mock_get_sentiment.return_value = 'Sentiment analysis.'

        # Test lowercase
        response1 = self.client.get('/api/ai/news-sentiment/aapl')
        # Test uppercase
        response2 = self.client.get('/api/ai/news-sentiment/AAPL')

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_with_special_characters_in_symbol(self, mock_get_sentiment, mock_ensure_ollama):
        """Test news sentiment with special characters in symbol (e.g., BRK.B)."""
        mock_get_sentiment.return_value = 'Sentiment for BRK.B.'

        response = self.client.get('/api/ai/news-sentiment/BRK.B')

        self.assertEqual(response.status_code, 200)
        mock_get_sentiment.assert_called_with('BRK.B')


if __name__ == '__main__':
    unittest.main()
