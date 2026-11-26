"""Focused coverage tests for AI routes and their flow.py implementations.

The AI route handlers are exercised end to end through FastAPI while the
underlying flow.py analysis functions run for real. yfinance data and the
Ollama chat client are mocked so the suite stays offline and deterministic.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flow_api


def _chat_reply(content: str) -> MagicMock:
    response = MagicMock()
    response.message.content = content
    return response


def _price_history_payload(days: int = 80) -> str:
    dates = pd.date_range("2024-01-01", periods=days, freq="D")
    closes = [100.0 + i for i in range(days)]
    frame = pd.DataFrame(
        {
            "Date": dates,
            "Open": closes,
            "High": [price + 1 for price in closes],
            "Low": [price - 1 for price in closes],
            "Close": closes,
            "Volume": [1_000_000 + i * 1_000 for i in range(days)],
        }
    )
    return frame.to_json(orient="table")


class TestAIRouteCoverage(unittest.TestCase):
    """Exercise AI routes with mocked market data and LLM responses."""

    def setUp(self):
        self.client = TestClient(flow_api.app)

    def test_fundamental_analysis_route_builds_compact_summary(self):
        fundamentals = json.dumps(
            {
                "symbol": "AAPL",
                "marketCap": 3_000_000_000_000,
                "trailingPE": 28.5,
                "returnOnEquity": 0.45,
            }
        )
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data") as mock_set_cache,
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_fundamentals", return_value=fundamentals),
        ):
            mock_chat.return_value = _chat_reply("- Strong cash generation.")
            response = self.client.get("/api/ai/fundamental-analysis/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "- Strong cash generation.")
        mock_set_cache.assert_called_once()
        prompt = mock_chat.call_args.kwargs["messages"][1]["content"]
        self.assertIn("AAPL", prompt)
        self.assertIn("marketCapBillions", prompt)

    def test_fundamental_analysis_route_returns_503_when_flow_fails(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_fundamentals", side_effect=RuntimeError("upstream down")),
        ):
            response = self.client.get("/api/ai/fundamental-analysis/AAPL")

        self.assertEqual(response.status_code, 503)
        mock_chat.assert_not_called()

    def test_balance_sheet_analysis_route_keeps_valid_ai_lines(self):
        balance_sheet = {
            "2024-09-30": {
                "Total Assets": 1_000,
                "Total Liabilities": 400,
                "Stockholders Equity": 600,
                "Current Assets": 500,
                "Current Liabilities": 250,
                "Cash And Cash Equivalents": 100,
                "Total Debt": 200,
            }
        }
        analysis = (
            "Liquidity: current ratio 2.00\n"
            "Leverage: D/E 0.33\n"
            "Margin of Safety: equity 60% of assets\n"
            "Verdict: VALUE"
        )
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_balance_sheet", return_value=balance_sheet),
        ):
            mock_chat.return_value = _chat_reply(analysis)
            response = self.client.get("/api/ai/balance-sheet-analysis/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), analysis)

    def test_balance_sheet_analysis_route_renders_fallback_when_ai_text_invalid(self):
        balance_sheet = {
            "2024-09-30": {
                "Total Assets": 1_000,
                "Total Liabilities": 400,
                "Stockholders Equity": 600,
                "Current Assets": 500,
                "Current Liabilities": 250,
                "Cash And Cash Equivalents": 100,
            }
        }
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_balance_sheet", return_value=balance_sheet),
        ):
            mock_chat.return_value = _chat_reply("not the requested format")
            response = self.client.get("/api/ai/balance-sheet-analysis/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Liquidity:", response.json())
        self.assertIn("Verdict:", response.json())

    def test_balance_sheet_analysis_route_reports_missing_data(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_balance_sheet", return_value=None),
        ):
            response = self.client.get("/api/ai/balance-sheet-analysis/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertIn("unavailable", response.json())
        mock_chat.assert_not_called()

    def test_income_stmt_analysis_route_keeps_valid_ai_lines(self):
        income_stmt = {
            "2024-09-30": {
                "Total Revenue": 1_000,
                "Gross Profit": 400,
                "Operating Income": 200,
                "Net Income": 150,
                "Diluted EPS": 1.5,
            }
        }
        analysis = (
            "Revenue & Profitability: revenue $1,000, net $150\n"
            "Margins: gross 40%, operating 20%, net 15%\n"
            "Earnings: EPS 1.50\n"
            "Verdict: VALUE"
        )
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_quarterly_income_stmt", return_value=income_stmt),
        ):
            mock_chat.return_value = _chat_reply(analysis)
            response = self.client.get("/api/ai/income-stmt-analysis/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), analysis)

    def test_income_stmt_analysis_route_reports_missing_data(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_quarterly_income_stmt", return_value=None),
        ):
            response = self.client.get("/api/ai/income-stmt-analysis/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertIn("unavailable", response.json())
        mock_chat.assert_not_called()

    def test_technical_analysis_route_calculates_indicators(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_price_history", return_value=_price_history_payload()),
        ):
            mock_chat.return_value = _chat_reply("Uptrend with rising volume.")
            response = self.client.get("/api/ai/technical-analysis/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Uptrend with rising volume.")
        prompt = mock_chat.call_args.kwargs["messages"][1]["content"]
        self.assertIn("20-day SMA", prompt)

    def test_technical_analysis_route_returns_503_without_price_history(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_price_history", return_value=None),
        ):
            response = self.client.get("/api/ai/technical-analysis/AAPL")

        self.assertEqual(response.status_code, 503)
        mock_chat.assert_not_called()

    def test_action_recommendation_route_combines_inputs(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_ai_technical_analysis", return_value="Trend is up."),
            patch("flow.get_ai_fundamental_analysis", return_value="Cash is strong."),
            patch("flow.get_analyst_price_targets", return_value={"mean": 210}),
        ):
            mock_chat.return_value = _chat_reply("BUY")
            response = self.client.get("/api/ai/action-recommendation/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "BUY")
        prompt = mock_chat.call_args.kwargs["messages"][0]["content"]
        self.assertIn("Trend is up.", prompt)
        self.assertIn("Cash is strong.", prompt)

    def test_action_recommendation_route_returns_503_when_analysis_fails(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch(
                "flow.get_ai_technical_analysis",
                side_effect=RuntimeError("analysis down"),
            ),
            patch("flow.get_ai_fundamental_analysis", return_value="Cash is strong."),
            patch("flow.get_analyst_price_targets", return_value={"mean": 210}),
        ):
            response = self.client.get("/api/ai/action-recommendation/AAPL")

        self.assertEqual(response.status_code, 503)
        mock_chat.assert_not_called()

    def test_action_recommendation_sentence_route_summarizes(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch(
                "flow.get_ai_action_recommendation",
                return_value="BUY because fundamentals are strong.",
            ),
        ):
            mock_chat.return_value = _chat_reply("Buy AAPL for long-term value.")
            response = self.client.get("/api/ai/action-recommendation-sentence/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Buy AAPL for long-term value.")

    def test_action_recommendation_word_route_returns_single_word(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch(
                "flow.get_ai_action_recommendation",
                return_value="BUY because fundamentals are strong.",
            ),
        ):
            mock_chat.return_value = _chat_reply("BUY")
            response = self.client.get("/api/ai/action-recommendation-word/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "BUY")

    def test_news_sentiment_route_uses_flow_sentiment(self):
        news = [
            {"content": {"summary": "Company reports record earnings."}},
            {"content": {"summary": "Analysts raise price targets."}},
        ]
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_news", return_value=news),
        ):
            mock_chat.return_value = _chat_reply("The news is positive.")
            response = self.client.get("/api/ai/news-sentiment/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "The news is positive.")
        prompt = mock_chat.call_args.kwargs["messages"][0]["content"]
        self.assertIn("record earnings", prompt)

    def test_full_report_route_combines_analyses(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch("flow.get_ai_fundamental_analysis", return_value="Fundamentals."),
            patch("flow.get_ai_technical_analysis", return_value="Technicals."),
            patch("flow.get_ai_action_recommendation", return_value="Action."),
            patch("flow.get_analyst_price_targets", return_value={"mean": 210}),
        ):
            mock_chat.return_value = _chat_reply("Full report text.")
            response = self.client.get("/api/ai/full-report/AAPL")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Full report text.")
        prompt = mock_chat.call_args.kwargs["messages"][0]["content"]
        self.assertIn("Fundamentals.", prompt)
        self.assertIn("Technicals.", prompt)
        self.assertIn("Action.", prompt)

    def test_full_report_route_returns_503_when_component_fails(self):
        with (
            patch("db.get_cached_data", return_value=None),
            patch("db.set_cached_data"),
            patch("flow.ensure_ollama"),
            patch("flow._CHAT") as mock_chat,
            patch(
                "flow.get_ai_fundamental_analysis",
                side_effect=RuntimeError("fundamentals down"),
            ),
            patch("flow.get_ai_technical_analysis", return_value="Technicals."),
            patch("flow.get_ai_action_recommendation", return_value="Action."),
            patch("flow.get_analyst_price_targets", return_value={"mean": 210}),
        ):
            response = self.client.get("/api/ai/full-report/AAPL")

        self.assertEqual(response.status_code, 503)
        mock_chat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
