#!/bin/bash
IP='localhost'
curl "http://$IP:8000/fundamentals/ATT"
curl "http://$IP:8000/fundamentals/TSLA"
curl "http://$IP:8000/fundamentals/AMZN"
curl "http://$IP:8000/price_history/GOOG"
curl "http://$IP:8000/price_history/MSFT"
curl "http://$IP:8000/price_history/CHTR"
curl "http://$IP:8000/"
curl "http://$IP:8000""


endpoint="http://$IP:8000";
methods="fundamentals price_history"
tickers="CHTR GOOG MSFT TSLA AMZN IBM"

for ticker in $tickers; do
  for method in $methods; do
    curl "$endpoint/$method/$ticker" &
  done
  wait;
done

curl http://127.0.0.1:8000/price_history/ZBZZT
curl http://127.0.0.1:8000/tickers
