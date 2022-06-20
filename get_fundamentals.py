import yfinance as yf
import json
from pathlib import Path
from pandas import DataFrame

# tickers = ['^DJI', 'CHTR', 'GOOG']

with open('data/lists/ticker.list', "r") as ticker_file:
    tickers = ticker_file.readlines()

    for ticker in tickers:
        this_ticker = yf.Ticker(ticker)
        print(ticker)

        this_ticker_info = this_ticker.info

        ticker_file_name = ticker.strip() + '.json'
        path = Path.cwd() / 'data' / 'fundamentals' / ticker_file_name
        with open(path, "w") as this_ticker_file:
            this_ticker_file.write(json.dumps(this_ticker_info))
            this_ticker_file.close()

        for key,value in this_ticker_info.items():
            print(key, ':', value)
