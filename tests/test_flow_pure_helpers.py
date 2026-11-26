"""Unit tests for the pure helper functions in flow.py."""

import math
import os
import sys
import unittest
from datetime import datetime, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow


def _sample_price_df(days: int = 60) -> pd.DataFrame:
    base = datetime(2024, 1, 1)
    dates = [base + timedelta(days=i) for i in range(days)]
    close = [100 + i for i in range(days)]
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": [c - 0.3 for c in close],
            "High": [c + 0.8 for c in close],
            "Low": [c - 0.8 for c in close],
            "Close": close,
            "Volume": [1000 + i * 10 for i in range(days)],
        }
    )


class TestSafeFloat(unittest.TestCase):
    def test_numeric_values_are_converted(self):
        self.assertEqual(flow._safe_float("12.5"), 12.5)
        self.assertEqual(flow._safe_float(3), 3.0)
        self.assertEqual(flow._safe_float(-0.25), -0.25)

    def test_invalid_values_return_none(self):
        self.assertIsNone(flow._safe_float(None))
        self.assertIsNone(flow._safe_float("not-a-number"))
        self.assertIsNone(flow._safe_float(math.nan))
        self.assertIsNone(flow._safe_float(pd.NA))


class TestFormattingHelpers(unittest.TestCase):
    def test_format_money(self):
        self.assertEqual(flow._format_money(None), "n/a")
        self.assertEqual(flow._format_money(2_500_000_000), "$2.5B")
        self.assertEqual(flow._format_money(-1_200_000), "$-1.2M")
        self.assertEqual(flow._format_money(999), "$999")

    def test_format_ratio(self):
        self.assertEqual(flow._format_ratio(None), "n/a")
        self.assertEqual(flow._format_ratio(1.234), "1.23")
        self.assertEqual(flow._format_ratio(2), "2.00")


class TestLatestBalanceSheetSlice(unittest.TestCase):
    def test_none_and_invalid_inputs(self):
        self.assertEqual(flow._latest_balance_sheet_slice(None), (None, None))
        self.assertEqual(flow._latest_balance_sheet_slice("bad"), (None, None))
        self.assertEqual(
            flow._latest_balance_sheet_slice({"2024": [1, 2]}),
            ({"2024": [1, 2]}, "latest"),
        )

    def test_dataframe_uses_latest_period(self):
        frame = pd.DataFrame(
            {"Total Assets": [100.0, 120.0]},
            index=["2023-12-31", "2024-12-31"],
        )
        metrics, period = flow._latest_balance_sheet_slice(frame)
        self.assertEqual(period, "2024-12-31")
        self.assertEqual(metrics, {"Total Assets": 120.0})

    def test_period_dict_uses_latest_date(self):
        balance_sheet = {
            "2023-12-31": {"Total Assets": 100.0},
            "2024-12-31": {"Total Assets": 120.0},
        }
        metrics, period = flow._latest_balance_sheet_slice(balance_sheet)
        self.assertEqual(period, "2024-12-31")
        self.assertEqual(metrics, {"Total Assets": 120.0})

    def test_flat_dict_is_labelled_latest(self):
        balance_sheet = {"Total Assets": 100.0}
        metrics, period = flow._latest_balance_sheet_slice(balance_sheet)
        self.assertEqual(period, "latest")
        self.assertEqual(metrics, {"Total Assets": 100.0})

    def test_empty_dict_is_labelled_latest(self):
        self.assertEqual(flow._latest_balance_sheet_slice({}), ({}, "latest"))


class TestSummarizeBalanceSheet(unittest.TestCase):
    def test_derives_metrics_and_ratios(self):
        balance_sheet = {
            "Total Assets": 1000,
            "Total Liab": 400,
            "Total Stockholder Equity": 600,
            "Total Current Assets": 300,
            "Total Current Liabilities": 200,
            "Cash And Cash Equivalents": 100,
            "Long Term Debt": 50,
            "Short Long Term Debt": 30,
        }
        metrics, period = flow._summarize_balance_sheet_for_prompt(balance_sheet)
        self.assertEqual(period, "latest")
        self.assertEqual(
            metrics,
            {
                "total_assets": 1000.0,
                "total_liabilities": 400.0,
                "equity": 600.0,
                "current_assets": 300.0,
                "current_liabilities": 200.0,
                "working_capital": 100.0,
                "cash": 100.0,
                "total_debt": 80.0,
                "net_debt": -20.0,
                "current_ratio": 1.5,
                "cash_ratio": 0.5,
                "debt_to_equity": 0.13,
            },
        )

    def test_explicit_total_debt_takes_precedence(self):
        balance_sheet = {
            "Total Stockholder Equity": 600,
            "Long Term Debt": 50,
            "Short Long Term Debt": 30,
            "Total Debt": 75,
        }
        metrics, _ = flow._summarize_balance_sheet_for_prompt(balance_sheet)
        self.assertEqual(metrics["total_debt"], 75.0)

    def test_empty_balance_sheet_returns_none(self):
        self.assertEqual(flow._summarize_balance_sheet_for_prompt({}), (None, "latest"))

    def test_alternative_key_names_are_supported(self):
        balance_sheet = {
            "TotalAssets": 500,
            "TotalLiab": 200,
            "Stockholder Equity": 300,
            "Current Assets": 150,
            "Current Liabilities": 100,
            "Cash": 50,
            "LongTermDebt": 25,
        }
        metrics, _ = flow._summarize_balance_sheet_for_prompt(balance_sheet)
        self.assertEqual(metrics["total_assets"], 500.0)
        self.assertEqual(metrics["total_liabilities"], 200.0)
        self.assertEqual(metrics["equity"], 300.0)
        self.assertEqual(metrics["working_capital"], 50.0)


class TestRenderBalanceSheetBullets(unittest.TestCase):
    def test_value_verdict_for_strong_balance_sheet(self):
        text = flow._render_balance_sheet_bullets(
            {
                "current_ratio": 2.0,
                "cash_ratio": 1.0,
                "working_capital": 100,
                "equity": 600,
                "total_assets": 1000,
                "total_liabilities": 400,
                "debt_to_equity": 0.5,
                "net_debt": -20,
                "total_debt": 80,
            }
        )
        expected = (
            "Liquidity: current ratio 2.00, cash ratio 1.00, "
            "positive working capital\n"
            "Leverage: D/E 0.50, net cash, equity positive\n"
            "Margin of Safety: equity 60% of assets, "
            "assets/liabilities 2.50x\n"
            "Verdict: VALUE"
        )
        self.assertEqual(text, expected)

    def test_inconclusive_verdict_for_weak_balance_sheet(self):
        text = flow._render_balance_sheet_bullets(
            {
                "current_ratio": 1.0,
                "working_capital": -50,
                "equity": -10,
                "total_assets": 0,
                "total_liabilities": 0,
                "debt_to_equity": 2.0,
                "net_debt": 50,
                "total_debt": 80,
            }
        )
        self.assertIn("working capital tight", text)
        self.assertIn("net debt present", text)
        self.assertIn("equity negative", text)
        self.assertTrue(text.endswith("Verdict: INCONCLUSIVE"))

    def test_missing_metrics_use_fallbacks(self):
        text = flow._render_balance_sheet_bullets({})
        expected = (
            "Liquidity: insufficient data on near-term coverage\n"
            "Leverage: unable to assess leverage\n"
            "Margin of Safety: limited without price or earnings\n"
            "Verdict: INCONCLUSIVE"
        )
        self.assertEqual(text, expected)


_BALANCE_SHEET_METRICS = {
    "current_ratio": 2.0,
    "working_capital": 100,
    "equity": 600,
    "total_assets": 1000,
    "total_liabilities": 400,
    "debt_to_equity": 0.5,
    "net_debt": -20,
    "total_debt": 80,
}


class TestCoerceBalanceSheetResponse(unittest.TestCase):
    def test_valid_four_line_response_is_kept(self):
        raw = (
            "Liquidity: current ratio 2.00\n"
            "Leverage: D/E 0.50\n"
            "Margin of Safety: equity 60% of assets\n"
            "Verdict: VALUE"
        )
        self.assertEqual(
            flow._coerce_balance_sheet_response(_BALANCE_SHEET_METRICS, raw), raw
        )

    def test_short_response_is_replaced(self):
        expected = flow._render_balance_sheet_bullets(_BALANCE_SHEET_METRICS)
        self.assertEqual(
            flow._coerce_balance_sheet_response(
                _BALANCE_SHEET_METRICS, "Liquidity: ok\nVerdict: VALUE"
            ),
            expected,
        )

    def test_wrong_labels_are_replaced(self):
        expected = flow._render_balance_sheet_bullets(_BALANCE_SHEET_METRICS)
        raw = "Alpha: one\nBeta: two\nGamma: three\nDelta: four"
        self.assertEqual(
            flow._coerce_balance_sheet_response(_BALANCE_SHEET_METRICS, raw), expected
        )

    def test_overlong_response_is_replaced(self):
        expected = flow._render_balance_sheet_bullets(_BALANCE_SHEET_METRICS)
        filler = "word " * 31
        raw = (
            f"Liquidity: {filler}\n"
            f"Leverage: {filler}\n"
            f"Margin of Safety: {filler}\n"
            f"Verdict: {filler}"
        )
        self.assertEqual(
            flow._coerce_balance_sheet_response(_BALANCE_SHEET_METRICS, raw), expected
        )

    def test_missing_response_is_rendered(self):
        expected = flow._render_balance_sheet_bullets(_BALANCE_SHEET_METRICS)
        self.assertEqual(
            flow._coerce_balance_sheet_response(_BALANCE_SHEET_METRICS, None), expected
        )


class TestComputeTechnicalIndicators(unittest.TestCase):
    EXPECTED_KEYS = frozenset(
        {
            "sma_20",
            "sma_50",
            "rsi",
            "macd",
            "macd_signal",
            "bb_upper",
            "bb_lower",
            "bb_mid",
            "volume_avg",
            "close_latest",
            "volume_latest",
        }
    )

    def test_computes_expected_indicator_values(self):
        indicators = flow._compute_technical_indicators(_sample_price_df(60))
        self.assertEqual(set(indicators), self.EXPECTED_KEYS)
        self.assertEqual(indicators["close_latest"], 159.0)
        self.assertEqual(indicators["volume_latest"], 1590.0)
        self.assertAlmostEqual(indicators["sma_20"], 149.5)
        self.assertAlmostEqual(indicators["sma_50"], 134.5)
        self.assertAlmostEqual(indicators["volume_avg"], 1495.0)
        self.assertEqual(indicators["rsi"], 100.0)
        self.assertGreater(indicators["macd"], 0)
        self.assertGreater(indicators["bb_upper"], indicators["bb_mid"])
        self.assertGreater(indicators["bb_mid"], indicators["bb_lower"])

    def test_insufficient_history_returns_none_values(self):
        indicators = flow._compute_technical_indicators(_sample_price_df(29))
        self.assertEqual(set(indicators), self.EXPECTED_KEYS)
        self.assertTrue(all(value is None for value in indicators.values()))

    def test_missing_columns_returns_none_values(self):
        frame = _sample_price_df(60).drop(columns=["Volume"])
        indicators = flow._compute_technical_indicators(frame)
        self.assertTrue(all(value is None for value in indicators.values()))

    def test_none_input_returns_none_values(self):
        indicators = flow._compute_technical_indicators(None)
        self.assertTrue(all(value is None for value in indicators.values()))


if __name__ == "__main__":
    unittest.main()
