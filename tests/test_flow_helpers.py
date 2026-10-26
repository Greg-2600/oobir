"""Unit tests for flow.py helper functions."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow


class TestFlowHelpers(unittest.TestCase):
    """Test cases for flow.py helper functions."""

    @patch("yfinance.Ticker")
    def test_get_recommendations_returns_dict(self, mock_ticker):
        """Test get_recommendations returns a dict-like structure."""
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = {
            "period": ["0m", "-1m"],
            "strongBuy": [6, 6],
            "buy": [18, 19],
        }
        mock_ticker.return_value.recommendations = mock_df

        result = flow.get_recommendations("AAPL")
        self.assertIsInstance(result, dict)
        self.assertIn("period", result)

    @patch("yfinance.Ticker")
    def test_get_recommendations_empty(self, mock_ticker):
        """Test get_recommendations returns None when empty."""
        mock_df = MagicMock()
        mock_df.empty = True
        mock_ticker.return_value.recommendations = mock_df

        result = flow.get_recommendations("AAPL")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_recommendations_error(self, mock_ticker):
        """Test get_recommendations returns None on exception."""
        mock_ticker.return_value.recommendations.side_effect = Exception("API Error")
        result = flow.get_recommendations("INVALID")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_institutional_holders_returns_dict(self, mock_ticker):
        """Test get_institutional_holders returns a dict-like structure."""
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = {
            "Holder": ["Blackrock"],
            "pctHeld": [0.0797],
        }
        mock_ticker.return_value.institutional_holders = mock_df

        result = flow.get_institutional_holders("AAPL")
        self.assertIsInstance(result, dict)
        self.assertIn("Holder", result)

    @patch("yfinance.Ticker")
    def test_get_institutional_holders_empty(self, mock_ticker):
        """Test get_institutional_holders returns None when empty."""
        mock_df = MagicMock()
        mock_df.empty = True
        mock_ticker.return_value.institutional_holders = mock_df

        result = flow.get_institutional_holders("AAPL")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_institutional_holders_error(self, mock_ticker):
        """Test get_institutional_holders returns None on exception."""
        mock_ticker.return_value.institutional_holders.side_effect = Exception(
            "API Error"
        )
        result = flow.get_institutional_holders("INVALID")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_insider_transactions_returns_dict(self, mock_ticker):
        """Test get_insider_transactions returns a dict-like structure."""
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = {
            "Insider": ["John Doe"],
            "Shares": [1000],
        }
        mock_ticker.return_value.insider_transactions = mock_df

        result = flow.get_insider_transactions("AAPL")
        self.assertIsInstance(result, dict)
        self.assertIn("Insider", result)

    @patch("yfinance.Ticker")
    def test_get_insider_transactions_empty(self, mock_ticker):
        """Test get_insider_transactions returns None when empty."""
        mock_df = MagicMock()
        mock_df.empty = True
        mock_ticker.return_value.insider_transactions = mock_df

        result = flow.get_insider_transactions("AAPL")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_insider_transactions_error(self, mock_ticker):
        """Test get_insider_transactions returns None on exception."""
        mock_ticker.return_value.insider_transactions.side_effect = Exception(
            "API Error"
        )
        result = flow.get_insider_transactions("INVALID")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_analyst_upgrades_downgrades_returns_dict(self, mock_ticker):
        """Test get_analyst_upgrades_downgrades returns a dict-like structure."""
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = {
            "Firm": ["MoffettNathanson"],
            "ToGrade": ["Neutral"],
        }
        mock_ticker.return_value.upgrades_downgrades = mock_df

        result = flow.get_analyst_upgrades_downgrades("AAPL")
        self.assertIsInstance(result, dict)
        self.assertIn("Firm", result)

    @patch("yfinance.Ticker")
    def test_get_analyst_upgrades_downgrades_empty(self, mock_ticker):
        """Test get_analyst_upgrades_downgrades returns None when empty."""
        mock_df = MagicMock()
        mock_df.empty = True
        mock_ticker.return_value.upgrades_downgrades = mock_df

        result = flow.get_analyst_upgrades_downgrades("AAPL")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_analyst_upgrades_downgrades_error(self, mock_ticker):
        """Test get_analyst_upgrades_downgrades returns None on exception."""
        mock_ticker.return_value.upgrades_downgrades.side_effect = Exception(
            "API Error"
        )
        result = flow.get_analyst_upgrades_downgrades("INVALID")
        self.assertIsNone(result)

    @patch("yfinance.Ticker")
    def test_get_option_chain_returns_dict(self, mock_ticker):
        """Test get_option_chain returns structured data."""
        mock_calls = MagicMock()
        mock_calls.to_dict.return_value = {
            "strike": [170, 175],
            "lastPrice": [5.0, 2.5],
        }
        mock_chain = MagicMock()
        mock_chain.calls = mock_calls
        mock_ticker.return_value.option_chain.return_value = mock_chain
        mock_ticker.return_value.options = ["2025-01-17"]

        result = flow.get_option_chain("AAPL")
        self.assertIsNotNone(result)

    @patch("yfinance.Ticker")
    def test_get_option_chain_error(self, mock_ticker):
        """Test get_option_chain returns None on exception."""
        mock_ticker.return_value.option_chain.side_effect = Exception("No options")
        result = flow.get_option_chain("INVALID")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
