"""Offline unit tests for flow market-data helpers.

yfinance screeners and ticker history are mocked so no network calls are made.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow


def _quote(symbol, **overrides):
    quote = {
        "symbol": symbol,
        "shortName": f"{symbol} Inc",
        "longName": f"{symbol} Corporation",
        "regularMarketPrice": 10.0,
        "regularMarketChange": 5.0,
        "regularMarketChangePercent": 5.0,
        "regularMarketVolume": 1000,
        "averageDailyVolume3Month": 900,
        "marketCap": 1_000_000,
        "exchange": "NMS",
        "quoteType": "EQUITY",
    }
    quote.update(overrides)
    return quote


def _history(closes, volumes=None):
    data = {"Close": closes}
    if volumes is not None:
        data["Volume"] = volumes
    return pd.DataFrame(data)


class TestGetMoneyFlowStocksDay(unittest.TestCase):
    """Cover the day-gainers/day-losers screener path."""

    @patch.object(flow.yf, "screener")
    def test_day_gainers_calculates_money_flow(self, mock_screener):
        mock_screener.screen.return_value = {
            "quotes": [
                _quote("AAA"),
                _quote(
                    "BBB",
                    regularMarketPrice=20.0,
                    regularMarketChange=-2.0,
                    regularMarketVolume=2000,
                ),
            ]
        }

        result = flow.get_money_flow_stocks("day", "in", limit=2)

        mock_screener.screen.assert_called_once_with("day_gainers", count=2)
        self.assertEqual([item["symbol"] for item in result], ["AAA", "BBB"])
        self.assertEqual(result[0]["moneyFlow"], 500.0)
        self.assertEqual(result[1]["moneyFlow"], 800.0)

    @patch.object(flow.yf, "screener")
    def test_day_losers_respects_limit(self, mock_screener):
        mock_screener.screen.return_value = {
            "quotes": [_quote("AAA"), _quote("BBB"), _quote("CCC")]
        }

        result = flow.get_money_flow_stocks("day", "out", limit=1)

        mock_screener.screen.assert_called_once_with("day_losers", count=1)
        self.assertEqual([item["symbol"] for item in result], ["AAA"])

    @patch.object(flow.yf, "screener")
    def test_missing_quote_fields_use_defaults(self, mock_screener):
        mock_screener.screen.return_value = {"quotes": [{"symbol": "EMPTY"}]}

        result = flow.get_money_flow_stocks("day", "in", limit=1)

        self.assertEqual(result[0]["moneyFlow"], 0)
        self.assertEqual(result[0]["shortName"], "")
        self.assertEqual(result[0]["quoteType"], "EQUITY")
        self.assertEqual(result[0]["regularMarketPrice"], 0)


class TestGetMoneyFlowStocksPeriods(unittest.TestCase):
    """Cover the multi-day most-actives screener path and skip rules."""

    @patch.object(flow.yf, "Ticker")
    @patch.object(flow.yf, "screener")
    def test_week_gainers_are_sorted_by_money_flow(self, mock_screener, mock_ticker):
        mock_screener.screen.return_value = {
            "quotes": [
                _quote("AAA"),
                _quote("BBB"),
                _quote("ETF", quoteType="ETF"),
            ]
        }

        def ticker_factory(symbol):
            ticker = MagicMock()
            if symbol == "AAA":
                ticker.history.return_value = _history(
                    [10.0, 11.0, 12.0], [100, 100, 100]
                )
                ticker.fast_info.last_price = 12.5
            else:
                ticker.history.return_value = _history(
                    [20.0, 19.0, 18.0], [200, 200, 200]
                )
                ticker.fast_info.last_price = 17.5
            return ticker

        mock_ticker.side_effect = ticker_factory

        result = flow.get_money_flow_stocks("week", "in", limit=10)

        mock_screener.screen.assert_called_once_with("most_actives", count=100)
        mock_ticker.assert_any_call("AAA")
        mock_ticker.assert_any_call("BBB")
        self.assertEqual(mock_ticker.call_count, 2)
        self.assertEqual([item["symbol"] for item in result], ["BBB", "AAA"])
        self.assertEqual(result[0]["moneyFlow"], 360.0)
        self.assertEqual(result[1]["moneyFlow"], 240.0)
        self.assertEqual(result[0]["regularMarketPrice"], 17.5)
        self.assertEqual(result[1]["regularMarketPrice"], 12.5)

    @patch.object(flow.yf, "Ticker")
    @patch.object(flow.yf, "screener")
    def test_direction_out_sorts_ascending(self, mock_screener, mock_ticker):
        mock_screener.screen.return_value = {"quotes": [_quote("AAA"), _quote("BBB")]}
        mock_ticker.side_effect = lambda symbol: MagicMock(
            history=MagicMock(
                return_value=_history(
                    [10.0, 11.0, 12.0] if symbol == "AAA" else [20.0, 19.0, 18.0],
                    [100, 100, 100] if symbol == "AAA" else [200, 200, 200],
                )
            ),
            fast_info=MagicMock(last_price=None),
        )

        result = flow.get_money_flow_stocks("week", "out", limit=10)

        self.assertEqual([item["symbol"] for item in result], ["AAA", "BBB"])
        self.assertEqual(result[0]["moneyFlow"], 240.0)
        self.assertEqual(result[1]["moneyFlow"], 360.0)
        self.assertEqual(result[0]["regularMarketPrice"], 12.0)

    @patch.object(flow.yf, "Ticker")
    @patch.object(flow.yf, "screener")
    def test_unknown_period_defaults_to_week(self, mock_screener, mock_ticker):
        mock_screener.screen.return_value = {"quotes": [_quote("AAA")]}
        ticker = MagicMock()
        ticker.history.return_value = _history([10.0, 11.0, 12.0], [100, 100, 100])
        ticker.fast_info.last_price = None
        mock_ticker.return_value = ticker

        flow.get_money_flow_stocks("decade", "in", limit=1)

        ticker.history.assert_called_once_with(period="5d", auto_adjust=True)

    @patch.object(flow.yf, "Ticker")
    @patch.object(flow.yf, "screener")
    def test_skips_incomplete_zero_and_failing_tickers(
        self, mock_screener, mock_ticker
    ):
        mock_screener.screen.return_value = {
            "quotes": [_quote("AAA"), _quote("SHORT"), _quote("ZERO"), _quote("ERR")]
        }

        def ticker_factory(symbol):
            ticker = MagicMock()
            if symbol == "AAA":
                ticker.history.return_value = _history(
                    [10.0, 11.0, 12.0], [100, 100, 100]
                )
                ticker.fast_info.last_price = None
            elif symbol == "SHORT":
                ticker.history.return_value = _history([10.0], [100])
            elif symbol == "ZERO":
                ticker.history.return_value = _history([0.0, 1.0, 2.0], [100, 100, 100])
            else:
                ticker.history.side_effect = RuntimeError("provider down")
            return ticker

        mock_ticker.side_effect = ticker_factory

        result = flow.get_money_flow_stocks("month", "in", limit=10)

        self.assertEqual([item["symbol"] for item in result], ["AAA"])

    @patch.object(flow.yf, "Ticker")
    @patch.object(flow.yf, "screener")
    def test_missing_volume_column_yields_zero_money_flow(
        self, mock_screener, mock_ticker
    ):
        mock_screener.screen.return_value = {"quotes": [_quote("AAA")]}
        ticker = MagicMock()
        ticker.history.return_value = _history([10.0, 11.0, 12.0])
        ticker.fast_info.last_price = 12.0
        mock_ticker.return_value = ticker

        result = flow.get_money_flow_stocks("week", "in", limit=1)

        self.assertEqual(result[0]["moneyFlow"], 0)
        self.assertEqual(result[0]["averageDailyVolume3Month"], 900)

    @patch.object(flow.yf, "screener")
    def test_no_equity_tickers_returns_empty_list(self, mock_screener):
        mock_screener.screen.return_value = {"quotes": [_quote("ETF", quoteType="ETF")]}

        self.assertEqual(flow.get_money_flow_stocks("week", "in"), [])

    @patch.object(flow.yf, "screener")
    def test_screener_failure_returns_none(self, mock_screener):
        mock_screener.screen.side_effect = RuntimeError("screener unavailable")

        self.assertIsNone(flow.get_money_flow_stocks("day", "in"))


class TestGetScreenUndervaluedLargeCaps(unittest.TestCase):
    """Cover the undervalued large-cap screener helper."""

    @patch.object(flow.yf, "screener")
    def test_returns_ticker_symbols(self, mock_screener):
        mock_screener.screen.return_value = {
            "quotes": [{"symbol": "AAA"}, {"symbol": "BBB"}]
        }

        self.assertEqual(flow.get_screen_undervalued_large_caps(), ["AAA", "BBB"])
        mock_screener.screen.assert_called_once_with("undervalued_large_caps")

    @patch.object(flow.yf, "screener")
    def test_failure_returns_none(self, mock_screener):
        mock_screener.screen.side_effect = RuntimeError("screener unavailable")

        self.assertIsNone(flow.get_screen_undervalued_large_caps())


if __name__ == "__main__":
    unittest.main()
