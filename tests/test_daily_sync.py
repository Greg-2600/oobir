"""Offline unit tests for scripts/daily_sync.py.

Database connections and yfinance calls are mocked so the daily sync helpers
can be exercised deterministically without a live TimescaleDB or network.
"""

import os
import sys
import unittest
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
from psycopg2.extras import Json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import daily_sync as sync

FIXED_NOW = datetime(2024, 1, 5, 12, 0, tzinfo=UTC)


class FixedDateTime(datetime):
    """Drop-in replacement for the module datetime with a frozen clock."""

    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW if tz is None else FIXED_NOW.astimezone(tz)


_UNSET = object()


def mock_conn(fetchall=_UNSET, fetchone=_UNSET):
    """Return a mocked connection whose cursor is usable as a context manager."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    if fetchall is not _UNSET:
        cursor.fetchall.return_value = fetchall
    if fetchone is not _UNSET:
        cursor.fetchone.return_value = fetchone
    return conn, cursor


def price_history(rows=2):
    """Build a small yfinance-shaped DataFrame with a timezone-aware index."""
    dates = pd.to_datetime([f"2024-01-0{day}" for day in range(2, rows + 2)], utc=True)
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(rows)],
            "High": [102.0 + i for i in range(rows)],
            "Low": [99.0 + i for i in range(rows)],
            "Close": [101.0 + i for i in range(rows)],
            "Volume": [1000 * (i + 1) for i in range(rows)],
            "Dividends": [0.0] * rows,
            "Stock Splits": [0.0] * rows,
        },
        index=dates,
    )


def price_rows(count):
    """Build TimescaleDB-shaped price rows for indicator recomputation."""
    start = datetime(2024, 1, 1, tzinfo=UTC)
    return [
        {"date": start + timedelta(days=i), "close": 100.0 + i, "volume": 1000 + i}
        for i in range(count)
    ]


class TestConnectionHelpers(unittest.TestCase):
    def test_get_conn_uses_defaults(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(sync.psycopg2, "connect") as connect,
        ):
            sync.get_conn()
        connect.assert_called_once_with(
            host="localhost",
            port=5432,
            dbname="oobir",
            user="oobir",
            password="oobir",
        )

    def test_get_conn_reads_environment(self):
        env = {
            "PGHOST": "timescale",
            "PGPORT": "6543",
            "PGDATABASE": "oobir_test",
            "PGUSER": "tester",
            "PGPASSWORD": "not-a-real-secret",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(sync.psycopg2, "connect") as connect,
        ):
            sync.get_conn()
        connect.assert_called_once_with(
            host="timescale",
            port=6543,
            dbname="oobir_test",
            user="tester",
            password="not-a-real-secret",
        )

    def test_get_tracked_tickers(self):
        conn, cursor = mock_conn(fetchall=[("AAPL",), ("MSFT",)])
        self.assertEqual(sync.get_tracked_tickers(conn), ["AAPL", "MSFT"])
        statement = cursor.execute.call_args.args[0]
        self.assertIn("price_history", statement)
        self.assertIn("fundamentals", statement)

    def test_get_last_date(self):
        last_date = datetime(2024, 1, 2, tzinfo=UTC)
        conn, cursor = mock_conn(fetchone=(last_date,))
        self.assertEqual(sync.get_last_date(conn, "AAPL"), last_date)
        self.assertEqual(cursor.execute.call_args.args[1], ("AAPL",))

    def test_get_last_date_without_history(self):
        conn, _ = mock_conn(fetchone=None)
        self.assertIsNone(sync.get_last_date(conn, "AAPL"))


class TestSyncPrices(unittest.TestCase):
    def test_full_history_when_no_prices_stored(self):
        conn, _ = mock_conn()
        ticker = MagicMock()
        ticker.history.return_value = price_history(2)
        with (
            patch.object(sync, "get_last_date", return_value=None),
            patch.object(sync.yf, "Ticker", return_value=ticker) as yf_ticker,
            patch.object(sync, "execute_values") as execute_values,
        ):
            result = sync.sync_prices(conn, "AAPL")

        self.assertEqual(result, 2)
        yf_ticker.assert_called_once_with("AAPL")
        ticker.history.assert_called_once_with(period="max")
        statement, rows = execute_values.call_args.args[1:3]
        self.assertIn("ON CONFLICT", statement)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "AAPL")
        self.assertEqual(rows[0][1], datetime(2024, 1, 2, tzinfo=UTC))
        self.assertEqual(rows[0][4], 99.0)
        self.assertEqual(rows[0][6], 1000)
        conn.commit.assert_called_once()

    def test_incremental_fetch_starts_day_after_last_date(self):
        conn, _ = mock_conn()
        ticker = MagicMock()
        ticker.history.return_value = price_history(1)
        last_date = datetime(2024, 1, 3, tzinfo=UTC)
        with (
            patch.object(sync, "get_last_date", return_value=last_date),
            patch.object(sync, "datetime", FixedDateTime),
            patch.object(sync.yf, "Ticker", return_value=ticker),
            patch.object(sync, "execute_values"),
        ):
            self.assertEqual(sync.sync_prices(conn, "MSFT"), 1)
        ticker.history.assert_called_once_with(start="2024-01-04", end="2024-01-05")

    def test_already_current_skips_fetch(self):
        conn, _ = mock_conn()
        with (
            patch.object(sync, "get_last_date", return_value=FIXED_NOW),
            patch.object(sync, "datetime", FixedDateTime),
            patch.object(sync.yf, "Ticker") as yf_ticker,
            patch.object(sync, "execute_values") as execute_values,
        ):
            self.assertEqual(sync.sync_prices(conn, "AAPL"), 0)
        yf_ticker.assert_not_called()
        execute_values.assert_not_called()
        conn.commit.assert_not_called()

    def test_empty_or_missing_history_inserts_nothing(self):
        for history in (pd.DataFrame(), None):
            with self.subTest(history=history):
                conn, _ = mock_conn()
                ticker = MagicMock()
                ticker.history.return_value = history
                with (
                    patch.object(sync, "get_last_date", return_value=None),
                    patch.object(sync.yf, "Ticker", return_value=ticker),
                    patch.object(sync, "execute_values") as execute_values,
                ):
                    self.assertEqual(sync.sync_prices(conn, "AAPL"), 0)
                execute_values.assert_not_called()


class TestSyncFundamentals(unittest.TestCase):
    def test_convert_epoch(self):
        self.assertEqual(
            sync._convert_epoch(1704067200), datetime(2024, 1, 1, tzinfo=UTC)
        )
        for value in (0, -10, "2024-01-01", 1e300):
            with self.subTest(value=value):
                self.assertIsNone(sync._convert_epoch(value))

    def test_successful_refresh_upserts_mapped_fields(self):
        conn, cursor = mock_conn()
        info = {
            "regularMarketPrice": 123.0,
            "shortName": "Apple Inc.",
            "marketCap": 2_000_000_000_000,
            "exDividendDate": 1704067200,
        }
        ticker = MagicMock()
        ticker.info = info
        with (
            patch.object(sync.yf, "Ticker", return_value=ticker),
            patch.object(sync, "datetime", FixedDateTime),
        ):
            self.assertTrue(sync.sync_fundamentals(conn, "AAPL"))

        cursor.execute.assert_called_once()
        values = cursor.execute.call_args.args[1]
        self.assertEqual(values[0], "AAPL")
        self.assertEqual(values[1], FIXED_NOW)
        self.assertIsInstance(values[2], Json)
        self.assertIn("Apple Inc.", values)
        self.assertIn(2_000_000_000_000, values)
        self.assertIn(datetime(2024, 1, 1, tzinfo=UTC), values)
        self.assertEqual(info["_fetched_at"], FIXED_NOW.isoformat())
        conn.commit.assert_called_once()

    def test_missing_market_price_skips_upsert(self):
        conn, cursor = mock_conn()
        ticker = MagicMock()
        ticker.info = {"shortName": "No price"}
        with patch.object(sync.yf, "Ticker", return_value=ticker):
            self.assertFalse(sync.sync_fundamentals(conn, "AAPL"))
        cursor.execute.assert_not_called()
        conn.commit.assert_not_called()

    def test_yfinance_error_is_handled(self):
        conn, cursor = mock_conn()
        with patch.object(sync.yf, "Ticker", side_effect=RuntimeError("offline")):
            self.assertFalse(sync.sync_fundamentals(conn, "AAPL"))
        cursor.execute.assert_not_called()


class TestRecomputeIndicators(unittest.TestCase):
    def test_skips_when_pandas_missing(self):
        conn, _ = mock_conn()
        with (
            patch.object(sync, "HAS_PANDAS", False),
            patch.object(sync, "execute_values") as execute_values,
        ):
            self.assertEqual(sync.recompute_indicators(conn, "AAPL"), 0)
        execute_values.assert_not_called()

    def test_skips_when_price_history_too_short(self):
        conn, _ = mock_conn(fetchall=price_rows(49))
        with patch.object(sync, "execute_values") as execute_values:
            self.assertEqual(sync.recompute_indicators(conn, "AAPL"), 0)
        execute_values.assert_not_called()

    def test_computes_indicators_and_upserts_rows(self):
        conn, cursor = mock_conn(fetchall=price_rows(60))
        with (
            patch.object(sync, "execute_values") as execute_values,
            patch.object(sync.sql.Composed, "as_string", return_value="UPSERT SQL"),
        ):
            result = sync.recompute_indicators(conn, "AAPL")

        self.assertEqual(result, 41)
        statement, rows = execute_values.call_args.args[1:3]
        self.assertEqual(statement, "UPSERT SQL")
        self.assertEqual(len(rows), 41)
        self.assertEqual(rows[0][0], "AAPL")
        self.assertEqual(rows[0][1], datetime(2024, 1, 20, tzinfo=UTC))
        self.assertAlmostEqual(rows[0][2], 109.5)
        self.assertIsNone(rows[0][3])
        self.assertAlmostEqual(rows[0][4], 100.0)
        self.assertIsNotNone(rows[-1][3])
        self.assertIn("price_history", cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_args.args[1], ("AAPL",))
        conn.commit.assert_called_once()


class TestMain(unittest.TestCase):
    def test_prices_only_syncs_requested_tickers(self):
        conn = MagicMock()
        with (
            patch.object(sync, "get_conn", return_value=conn),
            patch("sys.argv", ["daily_sync.py", "aapl", "msft", "--prices-only"]),
            patch.object(sync, "sync_prices", return_value=2) as prices,
            patch.object(sync, "sync_fundamentals") as fundamentals,
            patch.object(sync, "recompute_indicators", return_value=3) as indicators,
        ):
            self.assertEqual(sync.main(), 0)
        self.assertEqual(prices.call_count, 2)
        self.assertEqual(
            [call.args[1] for call in prices.call_args_list], ["AAPL", "MSFT"]
        )
        fundamentals.assert_not_called()
        self.assertEqual(indicators.call_count, 2)
        conn.close.assert_called_once()

    def test_fundamentals_only_skips_price_and_indicator_phases(self):
        conn = MagicMock()
        with (
            patch.object(sync, "get_conn", return_value=conn),
            patch("sys.argv", ["daily_sync.py", "--fundamentals-only"]),
            patch.object(sync, "get_tracked_tickers", return_value=["AAPL"]),
            patch.object(sync, "sync_prices") as prices,
            patch.object(sync, "sync_fundamentals", return_value=True) as fundamentals,
            patch.object(sync, "recompute_indicators") as indicators,
        ):
            self.assertEqual(sync.main(), 0)
        fundamentals.assert_called_once_with(conn, "AAPL")
        prices.assert_not_called()
        indicators.assert_not_called()
        conn.close.assert_called_once()

    def test_defaults_to_all_tracked_tickers(self):
        conn = MagicMock()
        with (
            patch.object(sync, "get_conn", return_value=conn),
            patch("sys.argv", ["daily_sync.py"]),
            patch.object(sync, "get_tracked_tickers", return_value=["AAPL", "MSFT"]),
            patch.object(sync, "sync_prices", return_value=0) as prices,
            patch.object(sync, "sync_fundamentals", return_value=False) as fundamentals,
            patch.object(sync, "recompute_indicators", return_value=0) as indicators,
        ):
            self.assertEqual(sync.main(), 0)
        self.assertEqual(prices.call_count, 2)
        self.assertEqual(fundamentals.call_count, 2)
        self.assertEqual(indicators.call_count, 2)

    def test_no_tracked_tickers_exits_successfully(self):
        conn = MagicMock()
        with (
            patch.object(sync, "get_conn", return_value=conn),
            patch("sys.argv", ["daily_sync.py"]),
            patch.object(sync, "get_tracked_tickers", return_value=[]),
            patch.object(sync, "sync_prices") as prices,
        ):
            self.assertEqual(sync.main(), 0)
        prices.assert_not_called()
        conn.close.assert_called_once()

    def test_phase_errors_are_reported_as_failure(self):
        for failing_phase in (
            "sync_prices",
            "sync_fundamentals",
            "recompute_indicators",
        ):
            with self.subTest(failing_phase=failing_phase):
                conn = MagicMock()
                patches = {
                    "sync_prices": patch.object(sync, "sync_prices", return_value=1),
                    "sync_fundamentals": patch.object(
                        sync, "sync_fundamentals", return_value=True
                    ),
                    "recompute_indicators": patch.object(
                        sync, "recompute_indicators", return_value=1
                    ),
                }
                patches[failing_phase] = patch.object(
                    sync, failing_phase, side_effect=RuntimeError("boom")
                )
                with ExitStack() as stack:
                    stack.enter_context(
                        patch.object(sync, "get_conn", return_value=conn)
                    )
                    stack.enter_context(patch("sys.argv", ["daily_sync.py", "AAPL"]))
                    for patcher in patches.values():
                        stack.enter_context(patcher)
                    self.assertEqual(sync.main(), 1)
                conn.rollback.assert_called_once()
                conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
