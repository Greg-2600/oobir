import yahoo_fin.stock_info as si

# get list of S&P 500 tickers
sp = si.tickers_sp500()
print (sp)

# pull data for each S&P stock
price_data = {ticker: si.get_data(ticker) for ticker in sp}
print(price_data)