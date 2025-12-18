#!/usr/bin/env python3
"""Stock analysis and AI-driven insights module using yfinance and Ollama.

This module provides functions to fetch financial data for stocks using yfinance,
perform technical and fundamental analysis, and generate AI-driven insights using
Ollama LLM integration.
"""
# pylint: disable=global-statement,import-outside-toplevel,no-member

import os
import sys
import json
import inspect
from datetime import date, datetime

import yfinance as yf
import pandas as pd

# Point ollama client to a remote host by default. Can be overridden with OLLAMA_HOST env var.
_default_ollama = os.environ.get("OLLAMA_HOST", "http://192.168.1.248:11434")
os.environ.setdefault("OLLAMA_HOST", _default_ollama)
os.environ.setdefault("OLLAMA_URL", _default_ollama)
os.environ.setdefault("OLLAMA_BASE_URL", _default_ollama)

# Defer importing `ollama.chat` until after any CLI `--host` override so the
# environment variables can be set first. `ensure_ollama()` will import and
# cache the `chat` callable in `_CHAT`.
_CHAT = None
_CHAT_RESPONSE = None

def ensure_ollama(host: str | None = None):
    """
    Initialize the Ollama client and configure the host environment variables.

    This function sets up the global Ollama chat client and ensures that
    OLLAMA_HOST, OLLAMA_URL, and OLLAMA_BASE_URL environment variables
    are properly configured for subsequent AI function calls.

    Parameters
    ----------
    host : str or None, optional
        The Ollama server URL (e.g., "http://localhost:11434").
        If provided, overrides any existing environment variables.
        If None, uses the existing OLLAMA_HOST env var or the default.

    Side Effects
    ------------
    - Sets OLLAMA_HOST, OLLAMA_URL, and OLLAMA_BASE_URL environment variables
    - Imports and initializes the global _chat function from ollama module
    - Initializes the global _ChatResponse type if available

    Notes
    -----
    - Should be called before any AI analysis functions
    - Safe to call multiple times; only imports ollama on first call
    - The default host is defined by _default_ollama module variable
    """
    global _CHAT, _CHAT_RESPONSE  # pylint: disable=global-statement,import-outside-toplevel
    if host:
        os.environ["OLLAMA_HOST"] = host
        os.environ["OLLAMA_URL"] = host
        os.environ["OLLAMA_BASE_URL"] = host

    # ensure defaults exist
    _host = os.environ.get("OLLAMA_HOST", _default_ollama)
    os.environ.setdefault("OLLAMA_HOST", _host)
    os.environ.setdefault("OLLAMA_URL", _host)
    os.environ.setdefault("OLLAMA_BASE_URL", _host)

    if _CHAT is None:
        from ollama import chat as _chat_fn  # pylint: disable=import-outside-toplevel,no-member
        try:
            from ollama import ChatResponse as _chat_resp  # pylint: disable=import-outside-toplevel,no-member
            _CHAT_RESPONSE = _chat_resp
        except Exception:  # pylint: disable=broad-except
            _CHAT_RESPONSE = None
        _CHAT = _chat_fn

# Suppress specific warnings by redirecting stderr
class DummyFile:  # pylint: disable=too-few-public-methods
    """Dummy file object to suppress warnings."""

    def write(self, x):
        """Discard written output."""


# Redirect stderr to suppress warnings
sys.stderr = DummyFile()


def get_fundamentals(ticker):
    """Retrieve company fundamentals for a given ticker and return them as a JSON string.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol to query via yfinance.Ticker.

    Returns
    -------
    str or None
        A JSON-formatted string containing the ticker's fundamentals (from yfinance.Ticker.info)
        on success, or None if an exception occurs.

    Side effects
    ------------
    - Catches and prints any exceptions encountered while fetching data.

    Notes
    -----
    - Requires the yfinance package and the json module.
    - yfinance.Ticker.info performs network I/O and may return incomplete data or raise exceptions.
    """
    try:
        yf_obj = yf.Ticker(ticker)
        fundamentals_json = json.dumps(yf_obj.info)
        return fundamentals_json

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching fundamentals: {exc}")
        return None


def get_price_history(ticker):
    """Retrieve the recent price history for a given ticker symbol and return it as a JSON string.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol accepted by yfinance (e.g., "AAPL", "MSFT").

    Returns
    -------
    str or None
        A JSON string containing the price history in "table" orientation if successful.
        Returns None if an error occurs while fetching or serializing the data.

    Notes
    -----
    - Uses yfinance.Ticker(ticker).history(period="121d") to request the last 121 days of data.
    - Calls pandas.set_option('display.max_rows', None) as a side effect.
    - On error, the function prints an error message and returns None.
    - Requires the `yfinance` and `pandas` packages to be imported as `yf` and `pd`, respectively.

    Example
    -------
    >>> json_str = get_price_history("AAPL")
    >>> isinstance(json_str, str)
    True
    """
    try:
        pd.set_option('display.max_rows', None)
        yf_obj = yf.Ticker(ticker)
        price_history = yf_obj.history(period="121d")
        price_history_json = price_history.to_json(orient="table")
        return price_history_json

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching price_history: {exc}")
        return None


def get_analyst_price_targets(ticker):
    """Retrieve analyst price targets for a given ticker symbol.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol understood by yfinance (e.g. "AAPL").

    Returns
    -------
    dict or object or None
                - dict: a dictionary representation of the analyst price targets
                    if conversion succeeds.
                - object: the original object returned by
                    yfinance.Ticker(...).analyst_price_targets (commonly a
                    pandas.DataFrame) if conversion to dict fails.
                - None: if an exception occurs while fetching data; an error
                    message is printed in this case.

    Notes
    -----
    - This function uses yfinance.Ticker(ticker).analyst_price_targets under the hood.
    - Exceptions raised by yfinance are caught; no exceptions are propagated.
    """
    try:
        yf_obj = yf.Ticker(ticker)
        analyst_price_targets = yf_obj.analyst_price_targets
        try:
            return dict(analyst_price_targets)
        except Exception:  # pylint: disable=broad-except
            return analyst_price_targets

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching analyst_price_targets: {exc}")
        return None


def get_calendar(ticker):
    """Retrieve the calendar for a given ticker.

    Parameters
    ----------
    ticker : str
        Ticker symbol (passed to yfinance.Ticker).

    Returns
    -------
    dict or None
        A dictionary representation of the ticker's calendar. The function attempts
        the following in order:
          1. Return calendar.to_dict() if available.
          2. Return a dict where any date or datetime values are converted to ISO
             8601 strings.
          3. Return dict(calendar) as a last resort.
        If an unexpected error occurs while fetching the calendar, the function
        prints an error message and returns None.

    Notes
    -----
    - This function suppresses most internal exceptions and prefers returning a
      dictionary or None rather than raising.
    - Date and datetime objects in the calendar are converted to ISO format when
      the direct to_dict() call is not available.
    """
    try:
        yf_obj = yf.Ticker(ticker)
        calendar = yf_obj.calendar
        try:
            return calendar.to_dict()  # pylint: disable=no-member
        except Exception:  # pylint: disable=broad-except
            try:
                return {
                    k: (v.isoformat() if isinstance(v, (date, datetime)) else v)
                    for k, v in dict(calendar).items()
                }
            except Exception:  # pylint: disable=broad-except
                return dict(calendar)

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching calendar: {exc}")
        return None


def get_quarterly_income_stmt(ticker):
    """Retrieve the quarterly income statement for a given ticker symbol using yfinance.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol passed to yfinance.Ticker.

    Returns
    -------
    dict | object | None
        - dict: A dictionary representation of the quarterly income statement when
          the underlying object's `.to_dict()` call succeeds.
        - object: The raw object returned by yfinance (commonly a pandas DataFrame)
          if `.to_dict()` raises an exception.
        - None: If an error occurs while initializing yfinance.Ticker or accessing
          the quarterly income statement; an error message is printed to stdout.

    Notes
    -----
    - This function catches exceptions raised by yfinance and by `.to_dict()`. It
      prints an error message on failure and returns None.
    """
    try:
        yf_obj = yf.Ticker(ticker)
        quarterly_income_stmt = yf_obj.quarterly_income_stmt
        try:
            # Convert Timestamp index to string to make it JSON-serializable
            quarterly_income_stmt.index = quarterly_income_stmt.index.astype(str)
            return quarterly_income_stmt.to_dict()
        except Exception:  # pylint: disable=broad-except
            return quarterly_income_stmt

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching quarterly_income_stmt: {exc}")
        return None


def get_option_chain(ticker):
    """Retrieve the option chain (calls) for a given ticker using yfinance.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g. "AAPL").

    Returns
    -------
    dict or list or object or None
        - If successful, attempts to return the calls option chain as a dict via
          DataFrame.to_dict().
        - If that conversion fails, attempts to return a list of record dicts
          (using _asdict or dict on each record).
        - If those conversions fail, returns the raw option_chain object as returned
          by yfinance.
        - Returns None if an exception occurs while fetching data (an error message
          is printed).

    Notes
    -----
    - Uses the first available expiration date (yf.Ticker(ticker).options[0]).
    - Requires the yfinance package. Conversions are best-effort and exceptions
      are swallowed to provide a fallback value.
    """
    try:
        yf_obj = yf.Ticker(ticker)
        option_chain = yf_obj.option_chain(yf_obj.options[0]).calls
        try:
            # Convert Timestamp index to string to make it JSON-serializable
            option_chain.index = option_chain.index.astype(str)
            return option_chain.to_dict()
        except Exception:  # pylint: disable=broad-except
            try:
                return [
                    r._asdict() if hasattr(r, '_asdict') else dict(r)
                    for r in option_chain
                ]
            except Exception:  # pylint: disable=broad-except
                return option_chain

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching option_chain: {exc}")
        return None


def get_news(ticker):
    """Retrieve news for a given ticker."""
    try:
        yf_obj = yf.Ticker(ticker)
        news = yf_obj.get_news(count=10, tab='news')
        return news

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching news: {exc}")
        return None


def get_balance_sheet(ticker):
    """Retrieve the annual balance sheet for a given ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol accepted by yfinance (e.g., "AAPL").

    Returns
    -------
    dict | pandas.DataFrame | None
        - dict: the balance sheet converted from a pandas.DataFrame via
          DataFrame.to_dict()
        - pandas.DataFrame: the raw DataFrame if conversion to dict fails
        - None: if an exception occurs while fetching the data

    Behavior
    --------
    - Uses yfinance.Ticker(ticker).get_balance_sheet() to obtain the balance sheet.
    - Sets pandas display.max_rows to None (affects global pandas settings).
    - Catches exceptions during fetch, prints an error message, and returns None.

    Examples
    --------
    >>> get_balance_sheet("AAPL")
    {'Total Assets': {...}, ...}
    """
    try:
        pd.set_option('display.max_rows', None)
        yf_obj = yf.Ticker(ticker)
        balance_sheet = yf_obj.get_balance_sheet()
        try:
            # Convert Timestamp index to string to make it JSON-serializable
            balance_sheet.index = balance_sheet.index.astype(str)
            return balance_sheet.to_dict()
        except Exception:  # pylint: disable=broad-except
            return balance_sheet

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching balance_sheet: {exc}")
        return None


def get_screen_undervalued_large_caps():
    """Retrieve stock screen of undervalued large cap stocks."""
    try:
        screen = yf.screen("undervalued_large_caps")
        tickers = [quote['symbol'] for quote in screen['quotes']]
        return tickers

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while fetching undervalued_large_caps: {exc}")
        return None



def get_ai_balance_sheet_analysis(ticker):
    """
    Generate an AI-driven analysis of a company's balance sheet.

    This function retrieves a company's balance sheet for the given ticker,
    ensures the local Ollama runtime is available, and sends a prompt to a
    configured LLM to produce valuation insights, fundamental analysis, and
    risk/reward commentary based on the retrieved balance sheet.

    Args:
        ticker (str): The security ticker symbol used to fetch the balance sheet.

    Returns:
        str or None: The textual analysis returned by the AI model on success,
        or None if an error occurred while fetching data or querying the model.

    Side effects:
        - Calls get_balance_sheet(ticker) to obtain financial data.
        - Calls ensure_ollama() to prepare the local LLM runtime.
        - Calls _chat(...) to send the prompt to the LLM; the prompt includes the
          retrieved balance sheet and instructs the model to adopt a specific
          expert persona.

    Errors:
        - Exceptions are caught internally; on exception the function prints an
          error message and returns None.

    Notes:
        - The prompt instructs the model to adopt the persona of a named historical
          investor. Output is AI-generated and may not reflect the views of that
          individual. Use the analysis as informational, not as definitive advice.
    """
    try:
        balance_sheet = get_balance_sheet(ticker)

        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'You are Benjamin Graham, a renowned value investor. '
                    'Please provide your expert insights and guidance on '
                    'valuation metrics, fundamental analysis, and potential '
                    f'risks and rewards {balance_sheet}.'
                ),
            }]
        )

        balance_sheet_analysis = getattr(response, 'message', response).content  # pylint: disable=no-member
        return balance_sheet_analysis

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing balance_sheet_analysis: {exc}")
        return None


def get_ai_fundamental_analysis(ticker):
    """Ask an AI to perform a fundamentals-based analysis for a given ticker.

    This function:
    - Retrieves fundamentals for the provided ticker via get_fundamentals(ticker).
    - Ensures the Ollama runtime is available (ensure_ollama()).
    - Sends a prompt to an AI model (configured to respond as "Benjamin Graham")
        to produce expert insights on valuation metrics, fundamental analysis,
        and potential risks and rewards.
    - Extracts and returns the AI-generated message content.

    Parameters:
            ticker (str): The ticker symbol to analyze.

    Returns:
            Optional[str]: The AI-generated fundamental analysis text on success;
            None if an error occurs.

    Side effects:
            - Calls get_fundamentals, ensure_ollama, and _CHAT (may perform network/IO).
            - Prints an error message and returns None if an exception is raised.

    Notes:
            The function catches all exceptions and does not propagate them to the caller.
    """
    try:
        fundamentals = get_fundamentals(ticker)

        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'You are Benjamin Graham, a renowned value investor. '
                    'Please provide your expert insights and guidance on '
                    'valuation metrics, fundamental analysis, and potential '
                    f'risks and rewards {fundamentals}.'
                ),
            }]
        )

        fundamental_analysis = getattr(response, 'message', response).content  # pylint: disable=no-member
        return fundamental_analysis

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing fundamental analysis: {exc}")
        return None


def get_ai_quarterly_income_stm_analysis(ticker):
    """Perform an AI-driven analysis of a company's quarterly income statement.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol whose quarterly income statement will be fetched
        and analyzed.

    Returns
    -------
    str or None
        The AI-generated analysis text of the quarterly income statement, or None
        if an error occurred.

    Behavior
    --------
    - Fetches financial data via get_quarterly_income_stmt(ticker).
    - Ensures the Ollama environment is available by calling ensure_ollama().
    - Sends a prompt (framed as the Benjamin Graham persona) and the fetched
      statement to the _CHAT model 'huihui_ai/llama3.2-abliterate:3b'.
    - Extracts and returns the returned chat message content.

    Errors
    ------
    All exceptions are caught; errors are printed to stdout and the function
    returns None.

    Security/Privacy Notes
    ----------------------
    - The raw quarterly income statement is included in the model prompt; sanitize
      or redact sensitive information if required.
    - Using a persona in prompts may produce stylistic or interpretive content
      rather than authoritative financial advice; validate any investment guidance
      independently.
    """
    try:
        quarterly_income_stm = get_quarterly_income_stmt(ticker)

        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'You are Benjamin Graham, a renowned value investor. '
                    'Please provide your expert insights and guidance on '
                    'valuation metrics, fundamental analysis, and potential '
                    f'risks and rewards {quarterly_income_stm}.'
                ),
            }]
        )

        quarterly_income_stm_analysis = getattr(response, 'message', response).content  # pylint: disable=no-member
        return quarterly_income_stm_analysis

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing income statement analysis: {exc}")
        return None


def get_ai_technical_analysis(ticker):
    """Perform AI-driven technical analysis on price data."""
    try:
        price_history = get_price_history(ticker)

        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'You are John Murphy, a renowned technical analyst. '
                    'Please conduct a technical analysis on this price data: '
                    f'{price_history}'
                ),
            }]
        )

        technical_analysis = getattr(response, 'message', response).content  # pylint: disable=no-member
        return technical_analysis

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing AI technical analysis: {exc}")
        return None


def get_ai_action_recommendation(ticker):
    """Generate AI recommendation to buy, sell, or hold a stock."""
    try:
        technical_analysis = get_ai_technical_analysis(ticker)
        fundamental_analysis = get_ai_fundamental_analysis(ticker)

        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'You are an expert and experienced stock broker specializing '
                    'in retirement accounts. Please analyze this information and '
                    'recommend to buy, sell, or hold: '
                    f'{ticker} {technical_analysis} {fundamental_analysis}'
                ),
            }]
        )

        action_analysis = getattr(response, 'message', response).content  # pylint: disable=no-member
        return action_analysis
    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing AI action recommendation: {exc}")
        return None


def get_ai_action_recommendation_sentence(ticker):
    """Generate AI recommendation as a single sentence."""
    try:
        action_analysis = get_ai_action_recommendation(ticker)
        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'You are an expert editor. Please summarize this into a single '
                    'sentence, including the most important information needed to '
                    'make an actionable decision about buying, selling, or holding. '
                    f'{action_analysis}'
                ),
            }]
        )

        action_recommendation_summary_sentence = getattr(
            response, 'message', response
        ).content  # pylint: disable=no-member
        return action_recommendation_summary_sentence

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing AI action recommendation: {exc}")
        return None


def get_ai_action_recommendation_single_word(ticker):
    """Generate AI recommendation as a single word (BUY, SELL, or HOLD)."""
    try:
        action_analysis = get_ai_action_recommendation(ticker)
        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'You are producing input to a software program. Please '
                    'summarize this into a single word: either BUY, SELL, or HOLD. '
                    'Do not use any punctuation, use only upper case letters, and '
                    'do not say anything other than the single word or you will '
                    f'cause software bugs. {action_analysis}'
                ),
            }]
        )

        action_recommendation_single_word = getattr(
            response, 'message', response
        ).content  # pylint: disable=no-member
        return action_recommendation_single_word

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing AI action recommendation: {exc}")
        return None


def get_ai_news_sentiment(ticker):
    """Analyze news sentiment for a ticker using AI."""
    try:
        news = get_news(ticker)
        if not news:
            return "No news available for analysis."
        
        # Extract summaries from news articles
        summaries = []
        for article in news:
            content = article.get('content', {})
            summary = content.get('summary', '')
            if summary:
                summaries.append(summary)
        
        if not summaries:
            return "No news summaries available for analysis."
        
        # Combine summaries for AI analysis
        combined_news = "\n".join(summaries[:5])  # Use top 5 articles
        
        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'Based on the following recent news summaries, determine if the overall '
                    'sentiment is good or bad for investors. Respond in a single sentence '
                    'summarizing whether the news is positive, negative, or neutral for the stock. '
                    f'News summaries:\n{combined_news}'
                ),
            }]
        )

        sentiment = getattr(response, 'message', response).content
        return sentiment

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while analyzing news sentiment: {exc}")
        return None


def get_ai_full_report(ticker):
    """Generate comprehensive AI report based on all available information."""
    try:
        fundamental_analysis = get_ai_fundamental_analysis(ticker)
        technical_analysis = get_ai_technical_analysis(ticker)
        action_analysis = get_ai_action_recommendation(ticker)
        analyst_price_targets = get_analyst_price_targets(ticker)

        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'I am seeking an expert-level analysis of my recent financial '
                    'report, requiring a high degree of technical knowledge and '
                    'experience in public company valuation. Please provide a '
                    'detailed breakdown of revenue growth, profitability, cash flow, '
                    'or balance sheet trends, along with recommendations for '
                    'improvement. Ensure that your analysis is grounded in the '
                    'latest industry research and best practices. '
                    f'{ticker} {fundamental_analysis} {technical_analysis} '
                    f'{action_analysis} {analyst_price_targets}'
                ),
            }]
        )

        full_report = getattr(response, 'message', response).content  # pylint: disable=no-member
        return full_report

    except Exception as exc:  # pylint: disable=broad-except
        print(f"An error occurred while performing AI full report creation: {exc}")
        return None



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run oobir analysis functions on a ticker"
    )
    parser.add_argument("ticker", nargs="?", help="Ticker symbol (e.g. AAPL)")
    parser.add_argument(
        "func",
        nargs="?",
        help="Function to call (default: get_ai_fundamental_analysis)",
        default="get_ai_fundamental_analysis"
    )
    parser.add_argument(
        "--host",
        help="Override OLLAMA host URL (e.g. http://192.168.1.248:11434)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available 'get_' functions and exit"
    )
    args = parser.parse_args()

    if args.list:
        current_module = sys.modules[__name__]
        funcs = [
            name for name, obj in inspect.getmembers(current_module, inspect.isfunction)
            if name.startswith('get_')
        ]
        for f in sorted(funcs):
            print(f)
        sys.exit(0)

    if not args.ticker:
        print("No ticker provided. Example: python flow.py AAPL get_ai_fundamental_analysis")
        sys.exit(1)

    func_name = args.func
    current_module = sys.modules[__name__]
    if not hasattr(current_module, func_name):
        print(f"Function '{func_name}' not found in module")
        sys.exit(1)

    func = getattr(current_module, func_name)
    # initialize ollama client with optional CLI host override
    ensure_ollama(getattr(args, 'host', None))
    try:
        result = func(args.ticker)
        # Print results sensibly
        if isinstance(result, (str, bytes)):
            print(result)
        else:
            try:
                print(json.dumps(result, default=str))
            except Exception:  # pylint: disable=broad-except
                print(repr(result))
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error running {func_name}: {exc}")
