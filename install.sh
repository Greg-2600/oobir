#!/bin/bash

deactivate

rm -rf ./venv

python3 -m venv venv

source venv/bin/activate

which python

pip install --upgrade pip
pip install -r requirements.txt
pip install yfinance --upgrade --no-cache-dir