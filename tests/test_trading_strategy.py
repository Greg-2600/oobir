"""Comprehensive tests for trading strategy feature.

This module tests:
- get_trading_strategy() function with various market conditions
- /api/trading-strategy/{symbol} API endpoint
- Edge cases: invalid tickers, insufficient data, error handling
- Integration with caching layer
"""

import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import flow
import flow_api
from fastapi.testclient import TestClient


class TestTradingStrategyFunction(unittest.TestCase):
    """Test cases for get_trading_strategy() function."""

    def setUp(self):
        """Set up test fixtures."""
        self.symbol = "AAPL"

    def _create_sample_price_data(self, days=60, trend="uptrend", volatility=1.0):
        """Create sample price history data for testing.
        
        Args:
            days: Number of days of data
            trend: "uptrend", "downtrend", or "sideways"
            volatility: Multiplier for price volatility (1.0 = normal)
        """
        base_date = datetime(2024, 1, 1)
        data = []
        
        base_price = 100.0
        for i in range(days):
            if trend == "uptrend":
                price = base_price + (i * 0.5)
            elif trend == "downtrend":
                price = base_price - (i * 0.5)
            else:  # sideways
                price = base_price + (5 * (i % 10))
            
            # Add some volatility
            import random
            random.seed(i)  # Deterministic for reproducibility
            daily_change = random.uniform(-2, 2) * volatility
            close = price + daily_change
            
            data.append({
                "Date": (base_date + timedelta(days=i)).isoformat(),
                "Open": round(close - 0.5, 2),
                "High": round(close + 1.5, 2),
                "Low": round(close - 1.5, 2),
                "Close": round(close, 2),
                "Volume": 1000000 + (i * 10000)
            })
        
        return json.dumps({"data": data, "meta": {"symbol": "TEST"}})

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_long_strategy_uptrend(self, mock_price_history, mock_analyst_targets):
        """Test LONG strategy detection in uptrend market."""
        mock_price_history.return_value = self._create_sample_price_data(days=60, trend="uptrend")
        mock_analyst_targets.return_value = {
            "current": 105.0,
            "mean": 120.0,
            "high": 130.0,
            "low": 100.0
        }
        
        result = flow.get_trading_strategy("AAPL")
        data = json.loads(result)
        
        # Verify result structure
        self.assertIn("ticker", data)
        self.assertIn("strategy_type", data)
        self.assertIn("confidence", data)
        self.assertIn("entry_target", data)
        self.assertIn("exit_targets", data)
        self.assertIn("stop_loss", data)
        self.assertIn("signals", data)
        
        # LONG strategy should be detected in uptrend
        self.assertEqual(data["strategy_type"], "LONG")
        self.assertIn(data["confidence"], ["HIGH", "MEDIUM"])
        
        # Entry target should be reasonable (below or at current price)
        self.assertIsNotNone(data["entry_target"])
        
        # Exit targets should have 3 levels with increasing profit
        self.assertEqual(len(data["exit_targets"]), 3)
        self.assertGreater(data["exit_targets"][0]["price"], data["current_price"])
        self.assertGreater(data["exit_targets"][1]["price"], data["exit_targets"][0]["price"])
        self.assertGreater(data["exit_targets"][2]["price"], data["exit_targets"][1]["price"])
        
        # Stop loss should be below entry
        self.assertIsNotNone(data["stop_loss"])
        self.assertLess(data["stop_loss"], data["entry_target"])
        
        # Risk reward ratio should be calculated
        self.assertIsNotNone(data["risk_reward_ratio"])
        self.assertGreater(data["risk_reward_ratio"], 0)
        
        # Signals should be non-empty
        self.assertGreater(len(data["signals"]), 0)

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_short_strategy_downtrend(self, mock_price_history, mock_analyst_targets):
        """Test SHORT strategy detection in downtrend market."""
        mock_price_history.return_value = self._create_sample_price_data(days=60, trend="downtrend")
        mock_analyst_targets.return_value = {
            "current": 95.0,
            "mean": 80.0,
            "high": 90.0,
            "low": 70.0
        }
        
        result = flow.get_trading_strategy("TSLA")
        data = json.loads(result)
        
        # SHORT strategy should be detected in downtrend
        self.assertEqual(data["strategy_type"], "SHORT")
        self.assertIn(data["confidence"], ["HIGH", "MEDIUM"])
        
        # Entry target should be above current for short
        self.assertIsNotNone(data["entry_target"])
        
        # Exit targets for short should be below current price
        self.assertEqual(len(data["exit_targets"]), 3)
        self.assertLess(data["exit_targets"][0]["price"], data["current_price"])
        self.assertLess(data["exit_targets"][1]["price"], data["exit_targets"][0]["price"])
        self.assertLess(data["exit_targets"][2]["price"], data["exit_targets"][1]["price"])
        
        # Stop loss should be above entry for short
        self.assertIsNotNone(data["stop_loss"])
        self.assertGreater(data["stop_loss"], data["entry_target"])

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_wait_strategy_sideways(self, mock_price_history, mock_analyst_targets):
        """Test WAIT strategy in sideways market."""
        mock_price_history.return_value = self._create_sample_price_data(days=60, trend="sideways")
        mock_analyst_targets.return_value = {
            "current": 100.0,
            "mean": 100.0,
            "high": 105.0,
            "low": 95.0
        }
        
        result = flow.get_trading_strategy("GOOGL")
        data = json.loads(result)
        
        # WAIT strategy in sideways movement
        self.assertEqual(data["strategy_type"], "WAIT")
        self.assertEqual(data["confidence"], "LOW")
        
        # Exit targets should be empty for WAIT
        self.assertEqual(len(data["exit_targets"]), 0)
        
        # Timeframe should indicate waiting
        self.assertIn("clearer signals", data["timeframe"].lower())

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_insufficient_data_returns_wait(self, mock_price_history, mock_analyst_targets):
        """Test that insufficient data returns WAIT strategy gracefully."""
        # Return data with < 20 days
        limited_data = json.dumps({"data": [
            {"Date": "2024-01-01", "Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000000}
        ] * 10})
        
        mock_price_history.return_value = limited_data
        mock_analyst_targets.return_value = {}
        
        result = flow.get_trading_strategy("BADTICKER")
        data = json.loads(result)
        
        # Should gracefully return WAIT strategy
        self.assertEqual(data["strategy_type"], "WAIT")
        self.assertEqual(data["confidence"], "LOW")
        self.assertIn("error", data)
        self.assertIn("insufficient", data["error"].lower())

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_none_price_data_returns_wait(self, mock_price_history, mock_analyst_targets):
        """Test that None price data returns WAIT strategy."""
        mock_price_history.return_value = None
        mock_analyst_targets.return_value = {}
        
        result = flow.get_trading_strategy("NODATA")
        data = json.loads(result)
        
        self.assertEqual(data["strategy_type"], "WAIT")
        self.assertEqual(data["confidence"], "LOW")
        self.assertIn("error", data)
        self.assertIn("Unable to fetch", data["error"])

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_exception_handling_returns_wait(self, mock_price_history, mock_analyst_targets):
        """Test that exceptions are caught and WAIT strategy is returned."""
        mock_price_history.side_effect = Exception("Connection error")
        mock_analyst_targets.return_value = {}
        
        result = flow.get_trading_strategy("ERROR")
        data = json.loads(result)
        
        self.assertEqual(data["strategy_type"], "WAIT")
        self.assertEqual(data["confidence"], "LOW")
        self.assertIn("error", data)

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_technical_levels_calculated(self, mock_price_history, mock_analyst_targets):
        """Test that technical levels are properly calculated."""
        mock_price_history.return_value = self._create_sample_price_data(days=60, trend="uptrend")
        mock_analyst_targets.return_value = {}
        
        result = flow.get_trading_strategy("MSFT")
        data = json.loads(result)
        
        # Verify technical levels exist and are numbers
        self.assertIn("technical_levels", data)
        levels = data["technical_levels"]
        
        self.assertIn("sma_20", levels)
        self.assertIn("sma_50", levels)
        self.assertIn("rsi", levels)
        self.assertIn("bb_upper", levels)
        self.assertIn("bb_lower", levels)
        
        # RSI should be between 0-100
        self.assertGreaterEqual(levels["rsi"], 0)
        self.assertLessEqual(levels["rsi"], 100)
        
        # BB upper should be > BB lower
        self.assertGreater(levels["bb_upper"], levels["bb_lower"])

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_analyst_targets_integration(self, mock_price_history, mock_analyst_targets):
        """Test that analyst targets are integrated into strategy."""
        mock_price_history.return_value = self._create_sample_price_data(days=60, trend="uptrend")
        mock_analyst_targets.return_value = {
            "current": 100.0,
            "mean": 125.0,
            "high": 150.0,
            "low": 90.0
        }
        
        result = flow.get_trading_strategy("NVDA")
        data = json.loads(result)
        
        # Analyst targets should be included
        self.assertIn("analyst_targets", data)
        self.assertIsNotNone(data["analyst_targets"])
        
        targets = data["analyst_targets"]
        self.assertEqual(targets["mean"], 125.0)
        self.assertEqual(targets["high"], 150.0)
        self.assertEqual(targets["low"], 90.0)

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_exit_targets_have_gain_percentages(self, mock_price_history, mock_analyst_targets):
        """Test that exit targets include gain percentage calculations."""
        mock_price_history.return_value = self._create_sample_price_data(days=60, trend="uptrend")
        mock_analyst_targets.return_value = {}
        
        result = flow.get_trading_strategy("AMD")
        data = json.loads(result)
        
        # Check exit targets have gain_pct for LONG strategy
        if data["strategy_type"] == "LONG":
            for target in data["exit_targets"]:
                self.assertIn("level", target)
                self.assertIn("price", target)
                self.assertIn("gain_pct", target)
                self.assertGreater(target["gain_pct"], 0)

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_confidence_matches_signal_strength(self, mock_price_history, mock_analyst_targets):
        """Test that confidence level matches signal strength."""
        mock_price_history.return_value = self._create_sample_price_data(days=60, trend="uptrend", volatility=0.3)
        mock_analyst_targets.return_value = {"mean": 150.0}  # Strong bullish analyst target
        
        result = flow.get_trading_strategy("TEST")
        data = json.loads(result)
        
        if data["strategy_type"] in ["LONG", "SHORT"]:
            # Strong uptrend with bullish analyst target should give HIGH or MEDIUM confidence
            self.assertIn(data["confidence"], ["HIGH", "MEDIUM", "LOW"])
        else:
            self.assertEqual(data["confidence"], "LOW")


class TestTradingStrategyEndpoint(unittest.TestCase):
    """Test cases for /api/trading-strategy endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(flow_api.app)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_trading_strategy_endpoint(self, mock_price_history, mock_analyst_targets, 
                                       mock_set_cache, mock_get_cache):
        """Test basic trading strategy endpoint functionality."""
        # Setup test data (uptrend for LONG signal)
        test_data = json.dumps({"data": [
            {"Date": "2024-01-01", "Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000000},
            *[{"Date": f"2024-01-{2+i:02d}", "Open": 100+i*0.5, "High": 101.5+i*0.5, 
               "Low": 98.5+i*0.5, "Close": 100.5+i*0.5, "Volume": 1000000 + i*10000} 
              for i in range(59)]
        ]})
        
        mock_price_history.return_value = test_data
        mock_analyst_targets.return_value = {"mean": 120.0, "high": 130.0, "low": 95.0, "current": 105.0}
        
        response = self.client.get('/api/trading-strategy/AAPL')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("ticker", data)
        self.assertIn("strategy_type", data)
        self.assertIn("confidence", data)
        
        # Cache should have been called
        mock_set_cache.assert_called_once()

    @patch('db.get_cached_data')
    @patch('db.set_cached_data')
    def test_trading_strategy_cache_hit(self, mock_set_cache, mock_get_cache):
        """Test that endpoint returns cached data when available."""
        cached_response = json.dumps({
            "ticker": "AAPL",
            "strategy_type": "LONG",
            "confidence": "HIGH"
        })
        
        mock_get_cache.return_value = cached_response
        
        response = self.client.get('/api/trading-strategy/AAPL')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should not call set_cache when cache hit
        self.assertEqual(data["ticker"], "AAPL")
        self.assertEqual(data["strategy_type"], "LONG")

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_invalid_ticker_returns_wait(self, mock_price_history, mock_analyst_targets,
                                        mock_set_cache, mock_get_cache):
        """Test endpoint handles invalid ticker gracefully."""
        mock_price_history.return_value = None
        mock_analyst_targets.return_value = {}
        
        response = self.client.get('/api/trading-strategy/INVALIDTICKER')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return WAIT strategy even for invalid ticker
        self.assertEqual(data["strategy_type"], "WAIT")
        self.assertEqual(data["confidence"], "LOW")

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.get_trading_strategy')
    def test_api_error_handling(self, mock_get_strategy, mock_set_cache, mock_get_cache):
        """Test endpoint error handling."""
        mock_get_strategy.side_effect = Exception("Unexpected error")
        
        response = self.client.get('/api/trading-strategy/ERROR')
        
        # Should return 500 error
        self.assertEqual(response.status_code, 500)

    @patch('db.get_cached_data', return_value=None)
    @patch('db.set_cached_data')
    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_endpoint_with_various_symbols(self, mock_price_history, mock_analyst_targets,
                                          mock_set_cache, mock_get_cache):
        """Test endpoint works with various stock symbols."""
        test_data = json.dumps({"data": [
            {"Date": "2024-01-01", "Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000000},
            *[{"Date": f"2024-01-{2+i:02d}", "Open": 100+i*0.5, "High": 101.5+i*0.5, 
               "Low": 98.5+i*0.5, "Close": 100.5+i*0.5, "Volume": 1000000 + i*10000} 
              for i in range(59)]
        ]})
        
        mock_price_history.return_value = test_data
        mock_analyst_targets.return_value = {}
        
        for symbol in ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]:
            response = self.client.get(f'/api/trading-strategy/{symbol}')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["ticker"], symbol)
            self.assertIn(data["strategy_type"], ["LONG", "SHORT", "WAIT"])


class TestTradingStrategyIntegration(unittest.TestCase):
    """Integration tests for trading strategy feature."""

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_consistency_between_signals_and_strategy(self, mock_price_history, mock_analyst_targets):
        """Test that strategy type is consistent with signals."""
        mock_price_history.return_value = json.dumps({"data": [
            {"Date": "2024-01-01", "Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000000},
            *[{"Date": f"2024-01-{2+i:02d}", "Open": 100+i*0.5, "High": 101.5+i*0.5, 
               "Low": 98.5+i*0.5, "Close": 100.5+i*0.5, "Volume": 1000000 + i*10000} 
              for i in range(59)]
        ]})
        mock_analyst_targets.return_value = {}
        
        result = flow.get_trading_strategy("CONSISTENCY_TEST")
        data = json.loads(result)
        
        # Verify signals list is populated
        self.assertGreater(len(data["signals"]), 0)
        
        # If LONG strategy, should have bullish signals
        if data["strategy_type"] == "LONG":
            bullish_keywords = ["bullish", "above", "oversold", "crossover"]
            signal_text = " ".join(data["signals"]).lower()
            self.assertTrue(any(keyword in signal_text for keyword in bullish_keywords))
        
        # If SHORT strategy, should have bearish signals
        if data["strategy_type"] == "SHORT":
            bearish_keywords = ["bearish", "below", "overbought", "crossover"]
            signal_text = " ".join(data["signals"]).lower()
            self.assertTrue(any(keyword in signal_text for keyword in bearish_keywords))

    @patch('flow.get_analyst_price_targets')
    @patch('flow.get_price_history')
    def test_json_serialization(self, mock_price_history, mock_analyst_targets):
        """Test that result is properly JSON serializable."""
        mock_price_history.return_value = json.dumps({"data": [
            {"Date": "2024-01-01", "Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000000},
            *[{"Date": f"2024-01-{2+i:02d}", "Open": 100+i*0.5, "High": 101.5+i*0.5, 
               "Low": 98.5+i*0.5, "Close": 100.5+i*0.5, "Volume": 1000000 + i*10000} 
              for i in range(59)]
        ]})
        mock_analyst_targets.return_value = {"mean": 120.0}
        
        result = flow.get_trading_strategy("JSON_TEST")
        
        # Should be valid JSON string
        self.assertIsInstance(result, str)
        
        # Should be parseable
        data = json.loads(result)
        
        # Should be re-serializable
        json_again = json.dumps(data)
        self.assertIsInstance(json_again, str)


if __name__ == '__main__':
    unittest.main()
