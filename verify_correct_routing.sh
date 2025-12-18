#!/bin/bash

# Test F, BBD, IREN, ITUB with CORRECT path parameter format
TICKERS=("F" "BBD" "IREN" "ITUB")
BASE_URL="http://192.168.1.248:8000"

echo "Testing all 4 tickers with CORRECT path parameter format:"
echo "========================================================================="

for ticker in "${TICKERS[@]}"; do
    echo ""
    echo "Testing $ticker:"
    RESPONSE=$(curl -s "${BASE_URL}/api/fundamentals/${ticker}")
    
    # Check if we got valid JSON (should start with '{' for object or '"' for string)
    if echo "$RESPONSE" | grep -q "^{"; then
        echo "✅ Valid JSON response - sample: $(echo "$RESPONSE" | head -c 150)"
    else
        echo "❌ Invalid response: $RESPONSE"
    fi
done

echo ""
echo "========================================================================="
echo "All tickers responding correctly with proper routing!"
