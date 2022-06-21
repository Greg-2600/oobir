#!/bin/bash

#curl "http://127.0.0.1:8000/fundamentals/ATT"
#curl "http://127.0.0.1:8000/fundamentals/TSLA"
#curl "http://127.0.0.1:8000/fundamentals/AMZN"
#curl http://127.0.0.1:8000/price_history/GOOG
#curl http://127.0.0.1:8000/price_history/MSFT
#curl http://127.0.0.1:8000/price_history/CHTR
curl http://127.0.0.1:8000/tickers


#endpoint='http://127.0.0.1:8000';
#methods='fundamentals price_history';
#tickers='CHTR GOOG MSFT TSLA AMZN IBM';

#for ticker in $tickers; do
#  echo "$ticker"
#  for method in $methods; do
#    echo "$endpoint $method"
#    curl "$endpoint$method$ticker"
#  done
# done

#curl http://127.0.0.1:8000/tickers
