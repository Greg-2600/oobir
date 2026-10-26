"""Tests for db_timescale.py with mocked TimescaleDB connection."""

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch


class TestDbTimescale(unittest.TestCase):
    """Tests for TimescaleDB helper functions."""

    def _mock_conn(self):
        return MagicMock()

    def test_get_ticker_date_range_returns_tuple(self):
        from db_timescale import get_ticker_date_range

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (
            datetime(2020, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 1, tzinfo=UTC),
        )

        result = get_ticker_date_range(mock_conn, "AAPL")
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], datetime(2020, 1, 1, tzinfo=UTC))
        self.assertEqual(result[1], datetime(2024, 1, 1, tzinfo=UTC))

    def test_get_ticker_date_range_none_values(self):
        from db_timescale import get_ticker_date_range

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (None, None)

        result = get_ticker_date_range(mock_conn, "INVALID")
        self.assertEqual(result, (None, None))

    def test_insert_price_history_rows_empty(self):
        from db_timescale import insert_price_history_rows

        mock_conn = self._mock_conn()
        result = insert_price_history_rows(mock_conn, [])
        self.assertEqual(result, 0)

    def test_insert_price_history_rows_success(self):
        from db_timescale import insert_price_history_rows

        mock_conn = self._mock_conn()
        result = insert_price_history_rows(mock_conn, [])
        self.assertEqual(result, 0)

    def test_fetch_price_history_basic(self):
        from db_timescale import fetch_price_history

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "date": datetime(2024, 1, 1, tzinfo=UTC),
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000000,
            "dividends": 0.0,
            "stock_splits": 0.0,
        }[key]

        mock_cursor.fetchall.return_value = [mock_row]

        result = fetch_price_history(mock_conn, "AAPL")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Close"], 103.0)
        self.assertEqual(result[0]["Volume"], 1000000)

    def test_fetch_price_history_with_limit(self):
        from db_timescale import fetch_price_history

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []

        result = fetch_price_history(mock_conn, "AAPL", limit=10)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_fetch_price_history_with_since_days(self):
        from db_timescale import fetch_price_history

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []

        result = fetch_price_history(mock_conn, "AAPL", since_days=30)
        self.assertIsInstance(result, list)

    def test_fetch_latest_fundamentals_not_found(self):
        from db_timescale import fetch_latest_fundamentals

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = None

        result = fetch_latest_fundamentals(mock_conn, "INVALID_TICKER")
        self.assertIsNone(result)

    def test_fetch_latest_fundamentals_bulk_with_none_tickers(self):
        from db_timescale import fetch_latest_fundamentals_bulk

        mock_conn = self._mock_conn()
        result = fetch_latest_fundamentals_bulk(mock_conn, [None, "", "  "])
        self.assertEqual(result, {})

    def test_fetch_latest_fundamentals_bulk_empty(self):
        from db_timescale import fetch_latest_fundamentals_bulk

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []

        result = fetch_latest_fundamentals_bulk(mock_conn, [])
        self.assertEqual(result, {})

        result = fetch_latest_fundamentals_bulk(mock_conn, ["", None, "  "])
        self.assertEqual(result, {})

    def test_list_fundamental_tickers(self):
        from db_timescale import list_fundamental_tickers

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("AAPL",), ("MSFT",), ("GOOGL",)]

        result = list_fundamental_tickers(mock_conn)
        self.assertEqual(result, ["AAPL", "MSFT", "GOOGL"])

    def test_fetch_technical_indicators_basic(self):
        from db_timescale import fetch_technical_indicators

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "date": datetime(2024, 1, 1, tzinfo=UTC),
            "sma_20": 150.0,
            "sma_50": 145.0,
            "rsi_14": 55.0,
            "macd": 2.5,
            "macd_signal": 2.0,
            "macd_histogram": 0.5,
            "bb_upper": 160.0,
            "bb_middle": 150.0,
            "bb_lower": 140.0,
            "volume_avg_20": 1000000.0,
            "volume_ratio": 1.2,
        }[key]

        mock_cursor.fetchall.return_value = [mock_row]

        result = fetch_technical_indicators(mock_conn, "AAPL")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rsi_14"], 55.0)
        self.assertEqual(result[0]["sma_20"], 150.0)

    def test_fetch_technical_indicators_with_limit(self):
        from db_timescale import fetch_technical_indicators

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []

        result = fetch_technical_indicators(mock_conn, "AAPL", limit=5)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_fetch_latest_technical_indicators_found(self):
        from db_timescale import fetch_latest_technical_indicators

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "date": datetime(2024, 1, 1, tzinfo=UTC),
            "sma_20": 150.0,
            "sma_50": 145.0,
            "rsi_14": 55.0,
            "macd": 2.5,
            "macd_signal": 2.0,
            "macd_histogram": 0.5,
            "bb_upper": 160.0,
            "bb_middle": 150.0,
            "bb_lower": 140.0,
            "volume_avg_20": 1000000.0,
            "volume_ratio": 1.2,
        }[key]

        mock_cursor.fetchall.return_value = [mock_row]

        result = fetch_latest_technical_indicators(mock_conn, "AAPL")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["rsi_14"], 55.0)

    def test_fetch_latest_technical_indicators_not_found(self):
        from db_timescale import fetch_latest_technical_indicators

        mock_conn = self._mock_conn()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []

        result = fetch_latest_technical_indicators(mock_conn, "INVALID")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
