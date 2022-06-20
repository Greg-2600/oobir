from Tickers import Generate_Tickers
from Fundamentals import YF_Fundamentals

this_tickers = Generate_Tickers.get_tickers()
print(this_tickers)

this_fundamentals = YF_Fundamentals
this_fundamentals('GOOG')
print(this_fundamentals)

#this_obj = {}
#this_obj[tickers] =

#print(this_obj)
