import yfinance as yf
import json
from pathlib import Path

# tickers = ['^DJI', 'CHTR', 'GOOG']

with open('data/lists/ticker.list', "r") as ticker_file:
    tickers = ticker_file.readlines()

    for ticker in tickers:
        this_ticker = yf.Ticker(ticker)
        #print(ticker)

        this_ticker_info = this_ticker.info

        path = Path.cwd() / 'data' / 'fundamentals' / ticker.strip()
        with open(path, "w") as this_ticker_file:
            this_ticker_file.write(json.dumps(this_ticker_info))
            this_ticker_file.close()

        for key,value in this_ticker_info.items():
            print(key, ':', value)

        #this_ticker_history = this_ticker.history(interval='1m', start='2022-04-02', end='2022-06-15')
        #print(this_ticker_history)


#pnl = this_ticker_info.financials
    #bs = this_ticker_info.balancesheet
    #cf = this_tickerinfo_.cashflow
    #fs = pd.concat([pnl,bs,cf])

    #print(this_ticker_info.institutional_holders)
    ##this_ticker_info.keys()
    #print(this_ticker_info['currentRatio'])
    ##print(this_ticker_info.get_financials())
    #print(fs)
#goog = yf.Ticker('goog')
#data = goog.history()
#data.head()
#print(data)
#data = yf.download(['GOOG','META'], period='1mo')
#data.head()
#print(data)