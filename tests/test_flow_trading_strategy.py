"""Deterministic unit tests for flow.get_trading_strategy.

The strategy engine combines price history with technical indicators. These
tests mock the data provider and the indicator calculation so the strategy
branching can be exercised offline without touching yfinance or Ollama.
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow


def _price_history(closes):
    """Build the JSON payload shape returned by flow.get_price_history."""
    base = datetime(2024, 1, 1)
    rows = [
        {"Date": (base + timedelta(days=index)).isoformat(), "Close": float(close)}
        for index, close in enumerate(closes)
    ]
    return json.dumps({"data": rows})


def _indicators(**overrides):
    """Return a complete indicator dict with deterministic defaults."""
    values = {
        "sma_20": 100.0,
        "sma_50": 95.0,
        "rsi": 50.0,
        "macd": 1.0,
        "macd_signal": 0.5,
        "bb_upper": 120.0,
        "bb_lower": 80.0,
    }
    values.update(overrides)
    return values


class TestGetTradingStrategy(unittest.TestCase):
    """Exercise the strategy calculation branches with mocked market data."""

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_missing_price_history_returns_wait(self, mock_price, mock_targets):
        mock_price.return_value = None
        mock_targets.return_value = None

        result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "WAIT")
        self.assertEqual(result["confidence"], "LOW")
        self.assertIn("Insufficient price data", result["signals"][0])
        self.assertIn("Unable to fetch price history", result["error"])

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_short_price_history_returns_wait(self, mock_price, mock_targets):
        mock_price.return_value = _price_history([100.0] * 10)
        mock_targets.return_value = None

        result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "WAIT")
        self.assertIn("Insufficient historical data", result["signals"][0])
        self.assertIn("at least 20 days", result["error"])

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_bullish_signals_produce_long_strategy(self, mock_price, mock_targets):
        mock_price.return_value = _price_history([110.0] * 25)
        mock_targets.return_value = {
            "high": 130.0,
            "low": 90.0,
            "mean": 115.0,
            "current": 110.0,
        }
        indicators = _indicators(
            sma_20=100.0,
            sma_50=90.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            bb_upper=120.0,
            bb_lower=80.0,
        )

        with patch("flow._compute_technical_indicators", return_value=indicators):
            result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "LONG")
        self.assertEqual(result["confidence"], "HIGH")
        self.assertEqual(result["entry_target"], 99.0)
        self.assertEqual(result["stop_loss"], 78.4)
        self.assertEqual(result["timeframe"], "1-3 months")
        self.assertEqual(result["exit_targets"][1]["price"], 115.0)
        self.assertEqual(result["exit_targets"][2]["price"], 130.0)
        self.assertEqual(result["risk_reward_ratio"], 0.16)
        self.assertEqual(result["analyst_targets"]["mean"], 115.0)
        self.assertEqual(result["technical_levels"]["sma_20"], 100.0)

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_bearish_signals_produce_short_strategy(self, mock_price, mock_targets):
        mock_price.return_value = _price_history([110.0] * 25)
        mock_targets.return_value = {
            "high": 150.0,
            "low": 80.0,
            "mean": 100.0,
            "current": 110.0,
        }
        indicators = _indicators(
            sma_20=120.0,
            sma_50=130.0,
            rsi=75.0,
            macd=0.5,
            macd_signal=1.0,
            bb_upper=105.0,
            bb_lower=80.0,
        )

        with patch("flow._compute_technical_indicators", return_value=indicators):
            result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "SHORT")
        self.assertEqual(result["confidence"], "HIGH")
        self.assertEqual(result["entry_target"], 105.0)
        self.assertEqual(result["stop_loss"], 133.9)
        self.assertEqual(result["timeframe"], "1-2 months")
        self.assertEqual(result["exit_targets"][1]["price"], 100.0)
        self.assertEqual(result["exit_targets"][2]["price"], 80.0)
        self.assertEqual(result["risk_reward_ratio"], 0.42)

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_mixed_signals_produce_wait_strategy(self, mock_price, mock_targets):
        mock_price.return_value = _price_history([105.0] * 25)
        mock_targets.return_value = None
        indicators = _indicators(
            sma_20=100.0,
            sma_50=110.0,
            rsi=75.0,
            macd=1.0,
            macd_signal=0.5,
            bb_upper=120.0,
            bb_lower=80.0,
        )

        with patch("flow._compute_technical_indicators", return_value=indicators):
            result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "WAIT")
        self.assertEqual(result["confidence"], "LOW")
        self.assertEqual(result["entry_target"], 105.0)
        self.assertIsNone(result["stop_loss"])
        self.assertEqual(result["exit_targets"], [])
        self.assertEqual(result["timeframe"], "Wait for clearer signals")
        self.assertIsNone(result["analyst_targets"])

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_oversold_below_lower_band_is_long_medium(self, mock_price, mock_targets):
        mock_price.return_value = _price_history([110.0] * 25)
        mock_targets.return_value = None
        indicators = _indicators(
            sma_20=120.0,
            sma_50=130.0,
            rsi=25.0,
            macd=1.0,
            macd_signal=0.5,
            bb_upper=130.0,
            bb_lower=115.0,
        )

        with patch("flow._compute_technical_indicators", return_value=indicators):
            result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "LONG")
        self.assertEqual(result["confidence"], "MEDIUM")
        self.assertIn("RSI oversold - potential buy", result["signals"])
        self.assertIn("Price below lower Bollinger Band - oversold", result["signals"])

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_approaching_oversold_below_sma_is_short_medium(
        self, mock_price, mock_targets
    ):
        mock_price.return_value = _price_history([105.0] * 25)
        mock_targets.return_value = None
        indicators = _indicators(
            sma_20=110.0,
            sma_50=100.0,
            rsi=35.0,
            macd=0.5,
            macd_signal=1.0,
            bb_upper=130.0,
            bb_lower=80.0,
        )

        with patch("flow._compute_technical_indicators", return_value=indicators):
            result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "SHORT")
        self.assertEqual(result["confidence"], "MEDIUM")
        self.assertIn("RSI approaching oversold", result["signals"])
        self.assertIn("Price below 20-day SMA", result["signals"])

    @patch("flow.get_analyst_price_targets")
    @patch("flow.get_price_history")
    def test_invalid_price_payload_returns_wait_error(self, mock_price, mock_targets):
        mock_price.return_value = "{not-json"
        mock_targets.return_value = None

        result = json.loads(flow.get_trading_strategy("AAPL"))

        self.assertEqual(result["strategy_type"], "WAIT")
        self.assertEqual(result["confidence"], "LOW")
        self.assertIn("Error generating strategy", result["signals"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
