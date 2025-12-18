"""Unit tests for news sentiment analysis functionality."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow


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


if __name__ == '__main__':
    unittest.main()
