"""Tests for technical indicator calculation and AI technical analysis flow."""

import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import pandas as pd

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow


class TestTechnicalIndicators(unittest.TestCase):
    def _sample_price_df(self, days: int = 60) -> pd.DataFrame:
        """Create a simple synthetic OHLCV DataFrame with upward trend and varying volume."""
        base = datetime(2024, 1, 1)
        dates = [base + timedelta(days=i) for i in range(days)]
        close = [100 + i * 0.5 for i in range(days)]  # steady uptrend
        open_ = [c - 0.3 for c in close]
        high = [c + 0.8 for c in close]
        low = [c - 0.8 for c in close]
        volume = [1_000_000 + (i % 10) * 50_000 for i in range(days)]

        df = pd.DataFrame({
            'Date': dates,
            'Open': open_,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume,
        })
        return df

    def test_calculate_technical_indicators_contains_expected_sections(self):
        df = self._sample_price_df(60)
        text = flow._calculate_technical_indicators(df)  # pylint: disable=protected-access
        self.assertIsInstance(text, str)
        self.assertIn('20-day SMA', text)
        self.assertIn('50-day SMA', text)
        self.assertIn('RSI (14)', text)
        self.assertIn('MACD', text)
        self.assertIn('Bollinger Bands', text)
        self.assertIn('Current Volume', text)
        self.assertIn('5-day High', text)

    @patch('flow._CHAT')
    @patch('flow.ensure_ollama')
    @patch('flow.get_price_history')
    def test_ai_technical_analysis_includes_indicators(self, mock_price, mock_ensure, mock_chat):
        # Build price history JSON similar to real endpoint structure
        df = self._sample_price_df(60)
        data_records = df.copy()
        data_records['Date'] = data_records['Date'].dt.strftime('%Y-%m-%d')
        payload = {
            'symbol': 'TEST',
            'data': data_records[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict(orient='records')
        }
        mock_price.return_value = json.dumps(payload)

        # Mock LLM response
        response = MagicMock()
        response.message.content = 'Analysis with indicators.'
        mock_chat.return_value = response

        result = flow.get_ai_technical_analysis('TEST')
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

        # Verify that indicators text was sent to the LLM prompt
        self.assertTrue(mock_chat.called)
        messages = mock_chat.call_args[1]['messages']
        # Expect a system message and a user message
        roles = [m['role'] for m in messages]
        self.assertIn('system', roles)
        self.assertIn('user', roles)
        user_msg = next(m for m in messages if m['role'] == 'user')
        self.assertIn('Analyze TEST technical setup', user_msg['content'])
        # The indicators block should contain SMA/RSI/MACD mentions
        self.assertRegex(user_msg['content'], r"20-day SMA|RSI \(14\)|MACD|Bollinger Bands")


if __name__ == '__main__':
    unittest.main()
