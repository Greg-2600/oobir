import yahoo_fin.stock_info as si

# get list of S&P 500 tickers
tickers_sp = si.tickers_sp500()
print(tickers_sp)

# pull data for each S&P stock
price_data = {ticker: si.get_data(ticker) for ticker in tickers_sp}
print(price_data)