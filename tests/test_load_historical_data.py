"""Offline unit tests for scripts/load_historical_data.py."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import load_historical_data as loader


class TestExtractRows(unittest.TestCase):
    def test_table_payload_preserves_zero_values(self):
        payload = {
            "data": [
                {
                    "Date": "2024-01-02T00:00:00.000Z",
                    "Open": 10.5,
                    "High": 11.0,
                    "Low": 10.0,
                    "Close": 10.75,
                    "Volume": 0,
                    "Dividends": 0.0,
                    "Stock Splits": 0.0,
                }
            ]
        }

        self.assertEqual(
            loader.extract_rows(payload, "AAPL"),
            [
                (
                    "AAPL",
                    "2024-01-02T00:00:00.000Z",
                    10.5,
                    11.0,
                    10.0,
                    10.75,
                    0,
                    0.0,
                    0.0,
                )
            ],
        )

    def test_history_and_prices_keys_are_accepted(self):
        item = {"date": "2024-01-03", "close": 12.0}
        self.assertEqual(
            loader.extract_rows({"history": [item]}, "MSFT"),
            [("MSFT", "2024-01-03", None, None, None, 12.0, None, None, None)],
        )
        self.assertEqual(
            loader.extract_rows({"prices": [item]}, "MSFT"),
            [("MSFT", "2024-01-03", None, None, None, 12.0, None, None, None)],
        )

    def test_lowercase_and_split_aliases(self):
        item = {
            "date": "2024-01-04",
            "open": 1,
            "high": 2,
            "low": 3,
            "close": 4,
            "volume": 5,
            "dividends": 6,
            "stock_splits": 7,
        }
        self.assertEqual(
            loader.extract_rows({"data": [item]}, "X"),
            [("X", "2024-01-04", 1, 2, 3, 4, 5, 6, 7)],
        )

        camel = {"Date": "2024-01-04", "StockSplits": 8}
        self.assertEqual(loader.extract_rows({"data": [camel]}, "X")[0][-1], 8)

    def test_no_usable_data_returns_empty_list(self):
        self.assertEqual(loader.extract_rows([], "AAPL"), [])
        self.assertEqual(loader.extract_rows({}, "AAPL"), [])
        self.assertEqual(loader.extract_rows({"data": {}}, "AAPL"), [])
        self.assertEqual(loader.extract_rows({"data": "not a list"}, "AAPL"), [])

    def test_non_dict_items_are_skipped(self):
        payload = {"data": ["bad", 123, None, {"Date": "2024-01-05", "Close": 9}]}
        rows = loader.extract_rows(payload, "AAPL")
        self.assertEqual(
            rows, [("AAPL", "2024-01-05", None, None, None, 9, None, None, None)]
        )


class TestTickerFromFilename(unittest.TestCase):
    def test_price_history_suffix_is_removed(self):
        self.assertEqual(
            loader.ticker_from_filename(Path("AAPL_price_history_all.json")), "AAPL"
        )

    def test_other_files_use_stem(self):
        self.assertEqual(
            loader.ticker_from_filename(Path("MSFT_fundamentals.json")),
            "MSFT_fundamentals",
        )


class TestIterFiles(unittest.TestCase):
    def test_returns_sorted_matching_files_only(self):
        with patch.object(
            Path, "glob", return_value=[Path("b.json"), Path("a.json")]
        ) as glob:
            files = loader.iter_files(Path("/data"))

        self.assertEqual(files, [Path("a.json"), Path("b.json")])
        glob.assert_called_once_with("*_price_history_all.json")


class TestGetConn(unittest.TestCase):
    def test_uses_environment_overrides(self):
        env = {
            "PGHOST": "db",
            "PGPORT": "6543",
            "PGDATABASE": "prices",
            "PGUSER": "reader",
            "PGPASSWORD": "secret",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(loader.psycopg2, "connect") as connect,
        ):
            loader.get_conn()

        connect.assert_called_once_with(
            host="db",
            port=6543,
            dbname="prices",
            user="reader",
            password="secret",
        )

    def test_uses_defaults_when_environment_is_empty(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(loader.psycopg2, "connect") as connect,
        ):
            loader.get_conn()

        connect.assert_called_once_with(
            host="localhost",
            port=5432,
            dbname="oobir",
            user="oobir",
            password="oobir",
        )


class TestLoadFile(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmp_dir.name) / "AAPL_price_history_all.json"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def write(self, payload):
        self.tmp.write_text(json.dumps(payload))

    def test_inserts_extracted_rows(self):
        self.write({"data": [{"Date": "2024-01-02", "Close": 5, "Volume": 0}]})
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur

        with (
            patch.object(loader, "execute_values") as execute_values,
            patch("builtins.print") as output,
        ):
            count = loader.load_file(conn, self.tmp)

        self.assertEqual(count, 1)
        execute_values.assert_called_once()
        sql, rows = execute_values.call_args.args[1:3]
        self.assertIn("ON CONFLICT (ticker, date) DO NOTHING", sql)
        self.assertEqual(
            rows, [("AAPL", "2024-01-02", None, None, None, 5, 0, None, None)]
        )
        output.assert_called_once_with("Loaded AAPL: 1 rows")

    def test_empty_file_is_skipped(self):
        self.write({"data": []})
        conn = MagicMock()

        with (
            patch.object(loader, "execute_values") as execute_values,
            patch("builtins.print") as output,
        ):
            count = loader.load_file(conn, self.tmp)

        self.assertEqual(count, 0)
        execute_values.assert_not_called()
        output.assert_called_once_with("Skip AAPL: no rows in file")


class TestMain(unittest.TestCase):
    def test_missing_data_dir_exits(self):
        with (
            patch.object(sys, "argv", ["prog", "--data-dir", "/does/not/exist"]),
            self.assertRaises(SystemExit),
        ):
            loader.main()

    def test_no_files_returns_zero(self):
        with (
            patch.object(sys, "argv", ["prog", "--data-dir", "/data"]),
            patch.object(loader.Path, "exists", return_value=True),
            patch.object(loader, "iter_files", return_value=[]),
            patch("builtins.print") as output,
        ):
            self.assertEqual(loader.main(), 0)

        output.assert_called_once_with("No files found in /data")

    def test_loads_every_file_and_commits(self):
        paths = [Path("a.json"), Path("b.json")]
        conn = MagicMock()
        with (
            patch.object(sys, "argv", ["prog", "--data-dir", "/data"]),
            patch.object(loader.Path, "exists", return_value=True),
            patch.object(loader, "iter_files", return_value=paths),
            patch.object(loader, "get_conn", return_value=conn),
            patch.object(loader, "load_file", side_effect=[2, 3]) as load_file,
            patch("builtins.print") as output,
        ):
            self.assertEqual(loader.main(), 0)

        self.assertEqual(load_file.call_count, 2)
        conn.__enter__.return_value.commit.assert_called_once_with()
        output.assert_called_once_with("Done. Inserted 5 rows.")


if __name__ == "__main__":
    unittest.main()
