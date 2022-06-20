import yahoo_fin.stock_info as si

class Price_History:
    def __init__(self, ticker):
        self.ticker = ticker
        self.price_data = {ticker: si.get_data(ticker)}

        print(self.price_data)