import yfinance as yf
import yahoo_fin.stock_info as si
import json

class YF_Fundamentals:
    def __init__(self, ticker):
        self.ticker_obj = yf.Ticker(ticker)
        self.data = self.ticker_obj.info
        print(self.data)