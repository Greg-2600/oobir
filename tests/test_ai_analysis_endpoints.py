"""Unit tests for AI analysis endpoints."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api
import flow


class TestAIAnalysisEndpoints(unittest.TestCase):
    """Test cases for AI analysis endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_fundamental_analysis')
    def test_fundamental_analysis_endpoint(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test fundamental analysis endpoint."""
        mock_analysis.return_value = 'Strong fundamentals with solid revenue growth.'

        response = self.client.get('/api/ai/fundamental-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        self.assertGreater(len(data), 0)
        mock_set_cache.assert_called_once()

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_fundamental_analysis')
    def test_fundamental_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test fundamental analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/fundamental-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_balance_sheet_analysis')
    def test_balance_sheet_analysis_endpoint(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test balance sheet analysis endpoint."""
        mock_analysis.return_value = 'Balance sheet shows healthy debt levels.'

        response = self.client.get('/api/ai/balance-sheet-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        mock_set_cache.assert_called_once()

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_balance_sheet_analysis')
    def test_balance_sheet_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test balance sheet analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/balance-sheet-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_quarterly_income_stm_analysis')
    def test_income_stmt_analysis_endpoint(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test income statement analysis endpoint."""
        mock_analysis.return_value = 'Revenue growth is impressive with expanding margins.'

        response = self.client.get('/api/ai/income-stmt-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        mock_set_cache.assert_called_once()

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_quarterly_income_stm_analysis')
    def test_income_stmt_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test income statement analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/income-stmt-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_technical_analysis')
    def test_technical_analysis_endpoint(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test technical analysis endpoint."""
        mock_analysis.return_value = 'Strong uptrend with support at $150.'

        response = self.client.get('/api/ai/technical-analysis/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        mock_set_cache.assert_called_once()

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_technical_analysis')
    def test_technical_analysis_endpoint_error(self, mock_analysis, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test technical analysis endpoint error handling."""
        mock_analysis.return_value = None

        response = self.client.get('/api/ai/technical-analysis/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation')
    def test_action_recommendation_endpoint(self, mock_recommendation, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test action recommendation endpoint."""
        mock_recommendation.return_value = 'BUY - Strong fundamentals with positive momentum.'

        response = self.client.get('/api/ai/action-recommendation/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        self.assertIn('BUY', data)
        mock_set_cache.assert_called_once()

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation')
    def test_action_recommendation_endpoint_error(self, mock_recommendation, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test action recommendation endpoint error handling."""
        mock_recommendation.return_value = None

        response = self.client.get('/api/ai/action-recommendation/TEST')

        self.assertEqual(response.status_code, 503)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation_sentence')
    def test_action_recommendation_sentence_endpoint(self, mock_rec_sentence, mock_ensure_ollama, mock_set_cache, mock_get_cache):
        """Test action recommendation sentence endpoint."""
        mock_rec_sentence.return_value = 'Buy AAPL for long-term value.'

        response = self.client.get('/api/ai/action-recommendation-sentence/AAPL')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, str)
        mock_set_cache.assert_called_once()

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.ensure_ollama')
    @patch('flow.get_ai_action_recommendation_sentence')
    def test_action_recommendation_sentence_endpoint_error(self, mock_rec_sentence, mock_ensure_ollama, mock_set_cache, mock_get_cache):
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


class TestGetNewsSentiment(unittest.TestCase):
    """Test cases for get_ai_news_sentiment function."""

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_with_valid_news(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test news sentiment analysis with valid news data."""
        # Mock news data
        mock_get_news.return_value = [
            {
                'content': {
                    'summary': 'Company reports strong quarterly earnings'
                }
            },
            {
                'content': {
                    'summary': 'Stock price reaches 52-week high'
                }
            }
        ]

        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.message.content = 'The sentiment is positive with strong earnings and price appreciation.'
        mock_chat.return_value = mock_response

        # Call function
        result = flow.get_ai_news_sentiment('AAPL')

        # Assertions
        self.assertIsNotNone(result)
        self.assertIn('positive', result.lower())
        mock_get_news.assert_called_once_with('AAPL')
        mock_ensure_ollama.assert_called_once()
        mock_chat.assert_called_once()

    @patch('flow.get_news')
    def test_news_sentiment_no_news_available(self, mock_get_news):
        """Test sentiment analysis when no news is available."""
        mock_get_news.return_value = []
        result = flow.get_ai_news_sentiment('XYZ')
        self.assertEqual(result, "No news available for analysis.")

    @patch('flow.get_news')
    def test_news_sentiment_no_summaries(self, mock_get_news):
        """Test sentiment analysis when articles have no summaries."""
        mock_get_news.return_value = [
            {'content': {}},
            {'content': {}}
        ]
        result = flow.get_ai_news_sentiment('XYZ')
        self.assertEqual(result, "No news summaries available for analysis.")

    @patch('flow.get_news')
    def test_news_sentiment_exception_handling(self, mock_get_news):
        """Test that exceptions are handled gracefully."""
        mock_get_news.side_effect = Exception("Network error")
        result = flow.get_ai_news_sentiment('AAPL')
        self.assertIsNone(result)

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_uses_top_5_articles(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test that only top 5 articles are used for analysis."""
        # Create 10 news items
        mock_get_news.return_value = [
            {'content': {'summary': f'News item {i}'}}
            for i in range(10)
        ]

        mock_response = MagicMock()
        mock_response.message.content = 'Analysis of sentiment'
        mock_chat.return_value = mock_response

        result = flow.get_ai_news_sentiment('AAPL')

        # Verify _CHAT was called with correct parameters
        mock_chat.assert_called_once()
        call_kwargs = mock_chat.call_args[1]
        self.assertEqual(call_kwargs['model'], 'huihui_ai/llama3.2-abliterate:3b')
        
        # Verify message structure
        messages = call_kwargs['messages']
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['role'], 'user')
        content = messages[0]['content']
        self.assertIn('sentiment', content.lower())

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_positive_response(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test sentiment analysis with positive news."""
        mock_get_news.return_value = [
            {'content': {'summary': 'Stock surges on positive guidance'}},
            {'content': {'summary': 'New product launch successful'}},
        ]

        mock_response = MagicMock()
        mock_response.message.content = 'The news is very positive for investors.'
        mock_chat.return_value = mock_response

        result = flow.get_ai_news_sentiment('TECH')
        self.assertIn('positive', result.lower())

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_negative_response(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test sentiment analysis with negative news."""
        mock_get_news.return_value = [
            {'content': {'summary': 'Company reports declining earnings'}},
            {'content': {'summary': 'Market share loss to competitors'}},
        ]

        mock_response = MagicMock()
        mock_response.message.content = 'The news is negative for investors.'
        mock_chat.return_value = mock_response

        result = flow.get_ai_news_sentiment('DECLINE')
        self.assertIn('negative', result.lower())

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_mixed_response(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test sentiment analysis with mixed news."""
        mock_get_news.return_value = [
            {'content': {'summary': 'Strong earnings but weak guidance'}},
        ]

        mock_response = MagicMock()
        mock_response.message.content = 'The sentiment is mixed with both positive and negative factors.'
        mock_chat.return_value = mock_response

        result = flow.get_ai_news_sentiment('MIXED')
        self.assertIsNotNone(result)

    @patch('flow.get_news')
    def test_news_sentiment_with_no_news(self, mock_get_news):
        """Test news sentiment when no news is available."""
        mock_get_news.return_value = []

        result = flow.get_ai_news_sentiment('UNKNOWN')

        self.assertEqual(result, 'No news available for analysis.')
        mock_get_news.assert_called_once_with('UNKNOWN')

    @patch('flow.get_news')
    def test_news_sentiment_with_no_summaries(self, mock_get_news):
        """Test news sentiment when articles have no summaries."""
        mock_get_news.return_value = [
            {'content': {}},
            {'content': {'summary': ''}},
        ]

        result = flow.get_ai_news_sentiment('TEST')

        self.assertEqual(result, 'No news summaries available for analysis.')

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_uses_top_five_articles(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test that only top 5 articles are used for analysis."""
        # Create 10 mock articles
        articles = [
            {
                'content': {
                    'summary': f'Article {i} summary'
                }
            }
            for i in range(10)
        ]
        mock_get_news.return_value = articles

        mock_response = MagicMock()
        mock_response.message.content = 'Mixed sentiment.'
        mock_chat.return_value = mock_response

        result = flow.get_ai_news_sentiment('TEST')

        # Verify the _CHAT call includes only 5 articles
        call_args = mock_chat.call_args
        messages = call_args[1]['messages']
        content = messages[0]['content']

        # Count how many article summaries are in the message
        article_count = sum(1 for i in range(5) if f'Article {i} summary' in content)
        self.assertEqual(article_count, 5)

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_error_handling(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test error handling in news sentiment analysis."""
        mock_get_news.return_value = [
            {'content': {'summary': 'Some news'}}
        ]
        mock_ensure_ollama.side_effect = Exception('Ollama connection failed')

        result = flow.get_ai_news_sentiment('TEST')

        self.assertIsNone(result)

    @patch('flow.get_news')
    @patch('flow.ensure_ollama')
    @patch('flow._CHAT')
    def test_news_sentiment_extracts_content_correctly(self, mock_chat, mock_ensure_ollama, mock_get_news):
        """Test that news sentiment correctly extracts content and summary."""
        mock_get_news.return_value = [
            {
                'content': {
                    'summary': 'Positive market reaction to new product launch',
                    'other_field': 'ignored'
                }
            },
            {
                'content': {
                    'summary': 'Analyst upgrades target price'
                }
            }
        ]

        mock_response = MagicMock()
        mock_response.message.content = 'Positive sentiment.'
        mock_chat.return_value = mock_response

        result = flow.get_ai_news_sentiment('TEST')

        self.assertIsNotNone(result)
        # Verify both summaries are in the chat request
        call_args = mock_chat.call_args
        messages = call_args[1]['messages']
        content = messages[0]['content']
        self.assertIn('Positive market reaction', content)
        self.assertIn('Analyst upgrades', content)


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
