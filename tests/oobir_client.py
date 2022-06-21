import json
import requests

TICKERS_API_URL = "http://127.0.0.1:8000/tickers"
tickers_response = requests.get(TICKERS_API_URL)

tickers = json.loads(tickers_response.json())

print(tickers)

for ticker in tickers:
    print(ticker)
    FUNDAMENTALS_API_URL = "http://127.0.0.1:8000/fundamentals/" + ticker
    fundamentals_response = requests.get(FUNDAMENTALS_API_URL)
    fundamentals = json.loads(fundamentals_response.json())
    print(fundamentals)

    PRICE_HISTORY_API_URL = "http://127.0.0.1:8000/price_history/" + ticker
    price_history_response = requests.get(PRICE_HISTORY_API_URL)
    price_history = json.loads(price_history_response.json())
    print(price_history)
