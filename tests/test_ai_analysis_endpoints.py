"""Unit tests for AI analysis endpoints."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


class TestAIAnalysisEndpoints(unittest.TestCase):
    """Test cases for AI analysis endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_fundamental_analysis')
    def test_fundamental_analysis_endpoint(self, mock_analysis, mock_ensure_ollama):
        """Test fundamental analysis endpoint."""
        mock_analysis.return_value = 'Strong fundamentals with solid revenue growth.'

        response = self.client.get('/api/ai/fundamental-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 0)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_fundamental_analysis')
    def test_fundamental_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama):
        """Test fundamental analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/fundamental-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_balance_sheet_analysis')
    def test_balance_sheet_analysis_endpoint(self, mock_analysis, mock_ensure_ollama):
        """Test balance sheet analysis endpoint."""
        mock_analysis.return_value = 'Balance sheet shows healthy debt levels.'

        response = self.client.get('/api/ai/balance-sheet-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_balance_sheet_analysis')
    def test_balance_sheet_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama):
        """Test balance sheet analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/balance-sheet-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_quarterly_income_stm_analysis')
    def test_income_stmt_analysis_endpoint(self, mock_analysis, mock_ensure_ollama):
        """Test income statement analysis endpoint."""
        mock_analysis.return_value = 'Revenue growth is impressive with expanding margins.'

        response = self.client.get('/api/ai/income-stmt-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_quarterly_income_stm_analysis')
    def test_income_stmt_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama):
        """Test income statement analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/income-stmt-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_technical_analysis')
    def test_technical_analysis_endpoint(self, mock_analysis, mock_ensure_ollama):
        """Test technical analysis endpoint."""
        mock_analysis.return_value = 'Strong uptrend with support at $150.'

        response = self.client.get('/api/ai/technical-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_technical_analysis')
    def test_technical_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama):
        """Test technical analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/technical-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation')
    def test_action_recommendation_endpoint(self, mock_recommendation, mock_ensure_ollama):
        """Test action recommendation endpoint."""
        mock_recommendation.return_value = 'BUY - Strong fundamentals with positive momentum.'

        response = self.client.get('/api/ai/action-recommendation/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        self.assertIn('BUY', data)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation')
    def test_action_recommendation_endpoint_error(self, mock_recommendation, mock_ensure_ollama):
        """Test action recommendation endpoint error handling."""
        mock_recommendation.return_value = None

        response = self.client.get('/api/ai/action-recommendation/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation_sentence')
    def test_action_recommendation_sentence_endpoint(self, mock_rec_sentence, mock_ensure_ollama):
        """Test action recommendation sentence endpoint."""
        mock_rec_sentence.return_value = 'Buy AAPL for long-term value.'

        response = self.client.get('/api/ai/action-recommendation-sentence/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation_sentence')
    def test_action_recommendation_sentence_endpoint_error(self, mock_rec_sentence, mock_ensure_ollama):
        """Test action recommendation sentence endpoint error handling."""
        mock_rec_sentence.return_value = None

        response = self.client.get('/api/ai/action-recommendation-sentence/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation_single_word')
    def test_action_recommendation_word_endpoint(self, mock_rec_word, mock_ensure_ollama):
        """Test action recommendation word endpoint."""
        mock_rec_word.return_value = 'BUY'

        response = self.client.get('/api/ai/action-recommendation-word/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        self.assertIn('BUY', data)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation_single_word')
    def test_action_recommendation_word_endpoint_error(self, mock_rec_word, mock_ensure_ollama):
        """Test action recommendation word endpoint error handling."""
        mock_rec_word.return_value = None

        response = self.client.get('/api/ai/action-recommendation-word/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_endpoint(self, mock_sentiment, mock_ensure_ollama):
        """Test news sentiment endpoint."""
        mock_sentiment.return_value = 'Overall positive sentiment from recent news.'

        response = self.client.get('/api/ai/news-sentiment/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_news_sentiment')
    def test_news_sentiment_endpoint_error(self, mock_sentiment, mock_ensure_ollama):
        """Test news sentiment endpoint error handling."""
        mock_sentiment.return_value = None

        response = self.client.get('/api/ai/news-sentiment/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_full_report')
    def test_full_report_endpoint(self, mock_report, mock_ensure_ollama):
        """Test full report endpoint."""
        mock_report.return_value = {
            'symbol': 'AAPL',
            'fundamental': 'Strong fundamentals',
            'technical': 'Positive trend',
            'recommendation': 'BUY'
        }

        response = self.client.get('/api/ai/full-report/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['symbol'], 'AAPL')
        self.assertIn('recommendation', data)

    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_full_report')
    def test_full_report_endpoint_error(self, mock_report, mock_ensure_ollama):
        """Test full report endpoint error handling."""
        mock_report.return_value = None

        response = self.client.get('/api/ai/full-report/TEST')

        self.assertEqual(response.status_code, 503)


if __name__ == '__main__':
    unittest.main()
