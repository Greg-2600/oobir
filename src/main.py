from fastapi import FastAPI
import yfinance as yf
import yahoo_fin.stock_info as si
import json
from functools import reduce

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "oobir is back"}




@app.get("/fundamentals/{ticker}")
async def read_item(ticker: str):
    ticker_obj = yf.Ticker(ticker)
    return {"ticker": ticker, "fundamentals": ticker_obj.info}

@app.get("/price_history/{ticker}")
async def read_item(ticker: str):
    price_history = si.get_data(ticker)
    result = price_history.to_json(orient="table")
    return {"ticker": ticker, "price_history": result}

@app.get("/tickers")
async def read_item():
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