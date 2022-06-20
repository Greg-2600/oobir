import yfinance as yf
import json
from pathlib import Path
from pandas import DataFrame

# tickers = ['^DJI', 'CHTR', 'GOOG']

with open('data/lists/ticker.list', "r") as ticker_file:
    tickers = ticker_file.readlines()

    for ticker in tickers:
        #this_ticker = yf.Ticker(ticker)
        #print(ticker)

        #this_ticker_info = this_ticker.info

        #ticker_file_name = ticker.strip() + '.json'
        #path = Path.cwd() / 'data' / 'fundamentals' / ticker_file_name
        #with open(path, "w") as this_ticker_file:
        #    this_ticker_file.write(json.dumps(this_ticker_info))
        #    this_ticker_file.close()

        #for key,value in this_ticker_info.items():
        #    print(key, ':', value)

        this_ticker_history = yf.download(ticker, start="2022-04-01", end="2022-06-19")
        print(str(this_ticker_history))

        test = this_ticker_history.to_json(orient='table')
        print(test)

        ticker_file_name = ticker.strip() + '.json'
        path = Path.cwd() / 'data' / 'history' / ticker_file_name
        with open(path, "w") as this_ticker_file:
            this_ticker_file.write(this_ticker_history)
            this_ticker_file.close()

        print(this_ticker_history)


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