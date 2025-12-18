#!/bin/bash

# Test F, BBD, IREN, ITUB only (skip VALE since we just tested it)
TICKERS=("F" "BBD" "IREN" "ITUB")
BASE_URL="http://192.168.1.248:8000"

for ticker in "${TICKERS[@]}"; do
    echo ""
    echo "========================================================================" 
    echo "Testing $ticker"
    echo "========================================================================"
    
    # Just test fundamentals for consistency check
    echo ""
    echo "Fundamentals for $ticker:"
    curl -s "${BASE_URL}/api/fundamentals?symbol=${ticker}" | head -c 800
    echo ""
    echo ""
done
