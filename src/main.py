# RUN ALL THE TESTS until py-test is implemented

import random
from Tickers import Generate_Tickers
from Fundamentals import YF_Fundamentals
from Price_History import Price_History

this_tickers = Generate_Tickers.get_tickers()
random_ticker = random.choice(this_tickers)
#print(this_tickers)

this_fundamentals = YF_Fundamentals
fundamentals = this_fundamentals(random_ticker)

this_price_history = Price_History
price_history = this_price_history(random_ticker)

#this_obj = {}
#this_obj[tickers] =

#print(this_obj)
