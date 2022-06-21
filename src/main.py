import fastapi
import yfinance as yf
import yahoo_fin.stock_info as si

app = fastapi.FastAPI()


@app.get("/")
async def get_hello_world():
    """Hello world, oobir is back"""
    return {"message": "Hello, World! oobir is back!"}


@app.get("/fundamentals/{ticker}")
async def get_fundamentals(ticker: str):
    """Given a valid ticker, fundamental analysis data is returned"""
    ticker_obj = yf.Ticker(ticker)
    return {"ticker": ticker, "fundamentals": ticker_obj.info}


@app.get("/price_history/{ticker}")
async def get_price_history(ticker: str):
    """Given a valid ticker, price history information is returned"""
    price_history = si.get_data(ticker)
    result = price_history.to_json(orient="table")
    return {"ticker": ticker, "price_history": result}


@app.get("/tickers")
async def get_tickers():
    """Returns all known valid tickers"""
    tickers_sp = si.tickers_sp500()
    tickers_dow = si.tickers_dow()
    tickers_nasdaq = si.tickers_nasdaq()
    tickers_other = si.tickers_other()
    tickers_all = []
    tickers_all.extend(tickers_sp)
    tickers_all.extend(tickers_dow)
    tickers_all.extend(tickers_nasdaq)
    tickers_all.extend(tickers_other)
    tickers_all_deduplicated = list(set(tickers_all))
    return {"ticker": "ALL", "result": tickers_all_deduplicated}
