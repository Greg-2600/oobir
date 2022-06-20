import yahoo_fin.stock_info as si

class Generate_Tickers:
    def __init__(self):
            pass

    def get_tickers():
        # instantiate all the list of tickers
        tickers_sp = si.tickers_sp500()
        tickers_dow = si.tickers_dow()
        tickers_nasdaq = si.tickers_nasdaq()
        tickers_other = si.tickers_other()

        # make a single dedeuplicated list
        tickers_all = []

        tickers_all.extend(tickers_sp)
        tickers_all.extend(tickers_dow)
        tickers_all.extend(tickers_nasdaq)
        tickers_all.extend(tickers_other)

        tickers_all_deduplicated = list(set(tickers_all))
        ##print(len(tickers_all))
        ##print(len(list(tickers_all_deduplicated)))

        # will return list of dedeuplicated tickers
        print(tickers_all_deduplicated)
        #return tickers_all_deduplicated

#obj = Tickers
#obj.main()