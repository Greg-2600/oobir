#!/bin/bash
# Test all API endpoints without piping - raw output

API="http://192.168.1.248:8000"
TICKERS=("F" "BBD" "IREN" "ITUB" "VALE")

echo "========================================================================"
echo "RAW API TEST - ALL ENDPOINTS"
echo "========================================================================"
echo ""

# Health checks
echo "Health Check:"
curl -s "$API/health"
echo ""
echo ""

echo "Ollama Health:"
curl -s "$API/health/ollama"
echo ""
echo ""

# Test each ticker
for ticker in "${TICKERS[@]}"; do
    echo "========================================================================"
    echo "TICKER: $ticker"
    echo "========================================================================"
    echo ""
    
    echo "Fundamentals:"
    curl -s "$API/api/fundamentals/$ticker"
    echo ""
    echo ""
    
    echo "Price History:"
    curl -s "$API/api/price-history/$ticker"
    echo ""
    echo ""
    
    echo "Analyst Targets:"
    curl -s "$API/api/analyst-targets/$ticker"
    echo ""
    echo ""
    
    echo "Calendar:"
    curl -s "$API/api/calendar/$ticker"
    echo ""
    echo ""
    
    echo "Income Statement:"
    curl -s "$API/api/income-stmt/$ticker"
    echo ""
    echo ""
    
    echo "Balance Sheet:"
    curl -s "$API/api/balance-sheet/$ticker"
    echo ""
    echo ""
    
    echo "Option Chain:"
    curl -s "$API/api/option-chain/$ticker"
    echo ""
    echo ""
    
    echo "News:"
    curl -s "$API/api/news/$ticker"
    echo ""
    echo ""
    
done

echo "========================================================================"
echo "END OF TESTS"
echo "========================================================================"
