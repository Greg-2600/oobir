import json
import requests
from pymongo import MongoClient
import pymongo

CONNECTION_STRING = "mongodb://microservice:A1d2r3i4a5n!@localhost:27017/"
client = MongoClient(CONNECTION_STRING)
db_tickers = client["tickers"]
db_fundamentals = client["fundamentals"]
db_price_history = client["price_history"]

TICKERS_API_URL = "http://localhost:8000/tickers"
tickers_response = requests.get(TICKERS_API_URL)
tickers = json.loads(tickers_response.json())
print(tickers)
print(client.list_database_names())
dblist = client.list_database_names()
if "tickers" in dblist:
    print("The database tickers exists.")

col = db_tickers["tickers"]
collist = db_tickers.list_collection_names()
if "tickers" in collist:
    print("The collection tickers exists.")

tickers_tx = col.insert_one({"tickers": tickers})
print(tickers_tx.inserted_id)

for ticker in tickers:
    print(ticker)
    FUNDAMENTALS_API_URL = "http://localhost:8000/fundamentals/" + ticker
    fundamentals_response = requests.get(FUNDAMENTALS_API_URL)
    fundamentals = json.loads(fundamentals_response.json())
    print(fundamentals)
    print(client.list_database_names())
    dblist = client.list_database_names()
    if "fundamentals" in dblist:
        print("The database fundamentals exists.")

    col = db_fundamentals["fundamentals"]
    collist = db_fundamentals.list_collection_names()
    if "fundamentals" in collist:
        print("The collection fundamentals exists.")

    fundamentals_tx = col.insert_one({ticker: fundamentals})
    print(fundamentals_tx.inserted_id)

    PRICE_HISTORY_API_URL = "http://localhost:8000/price_history/" + ticker
    price_history_response = requests.get(PRICE_HISTORY_API_URL)
    price_history = json.loads(price_history_response.json())
    print(price_history)
    db_price_history = client["price_history"]
    print(client.list_database_names())
    dblist = client.list_database_names()
    if "price_history" in dblist:
        print("The database price_history exists.")

    col = db_price_history["price_history"]
    collist = db_price_history.list_collection_names()
    if "price_history" in collist:
        print("The collection price_history exists.")

    price_history_tx = col.insert_one({ticker: price_history})
    print(price_history_tx.inserted_id)
