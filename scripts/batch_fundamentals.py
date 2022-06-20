import yfinance as yf
import json
from pathlib import Path
from pandas import DataFrame
import yahoo_fin.stock_info as si

# tickers = ['^DJI', 'CHTR', 'GOOG']

#analysts_data = si.get_analysts_info("amzn")
#print(analysts_data)
#holders = si.get_holders("amzn")
#info = holders["Top Institutional Holders"]
#print(info.Holder[0])
# print(this_ticker_info.institutional_holders)
##this_ticker_info.keys()
# print(this_ticker_info['currentRatio'])
##print(this_ticker_info.get_financials())
# print(fs)

with open('../data/lists/ticker.list', "r") as ticker_file:
    tickers = ticker_file.readlines()

    for ticker in tickers:
        this_ticker = yf.Ticker(ticker)
        print(ticker)

        this_ticker_info = this_ticker.info

        ticker_file_name = ticker.strip() + '.json'
        path = Path.cwd().parent / 'data' / 'fundamentals' / ticker_file_name
        with open(path, "w") as this_ticker_file:
            this_ticker_file.write(json.dumps(this_ticker_info))
            this_ticker_file.close()

        for key,value in this_ticker_info.items():
            print(key, ':', value)