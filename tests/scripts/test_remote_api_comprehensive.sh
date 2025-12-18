#!/bin/bash
# Comprehensive Remote API Test Suite
# Tests all endpoints against a remote API server
#
# Usage: ./test_remote_api_comprehensive.sh [OPTIONS]
# Options:
#   --api URL          API base URL (default: http://192.168.1.248:8000)
#   --tickers SYMBOLS  Comma-separated ticker symbols (default: F,BBD,IREN,ITUB,VALE)
#   --raw              Output raw JSON (no jq filtering)
#   --health-only      Only test health endpoints
#   --data-only        Only test data endpoints
#   --screening-only   Only test screening endpoint
#   --help             Show this help message

set -euo pipefail

# Defaults
API="${API:-http://192.168.1.248:8000}"
TICKERS="${TICKERS:-F,BBD,IREN,ITUB,VALE}"
RAW_OUTPUT=false
TEST_HEALTH=true
TEST_DATA=true
TEST_SCREENING=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api)
            API="$2"
            shift 2
            ;;
        --tickers)
            TICKERS="$2"
            shift 2
            ;;
        --raw)
            RAW_OUTPUT=true
            shift
            ;;
        --health-only)
            TEST_HEALTH=true
            TEST_DATA=false
            TEST_SCREENING=false
            shift
            ;;
        --data-only)
            TEST_HEALTH=false
            TEST_DATA=true
            TEST_SCREENING=false
            shift
            ;;
        --screening-only)
            TEST_HEALTH=false
            TEST_DATA=false
            TEST_SCREENING=true
            shift
            ;;
        --help)
            grep '^#' "$0" | head -20
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Convert tickers string to array
IFS=',' read -ra TICKER_ARRAY <<< "$TICKERS"

# Counters
PASSED=0
FAILED=0

# Helper to output with color
print_status() {
    local status=$1
    local message=$2
    if [[ "$status" == "pass" ]]; then
        echo -e "${GREEN}✅${NC} $message"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $message"
        ((FAILED++))
    fi
}

# Helper to test an endpoint
test_endpoint() {
    local ticker=$1
    local endpoint=$2
    local endpoint_name=$3
    
    local url="$API/api/$endpoint/$ticker"
    local response
    local http_code
    
    # Get response and HTTP code
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    response=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" == "200" ]]; then
        if [[ "$RAW_OUTPUT" == true ]]; then
            echo "  $endpoint_name:"
            echo "$response" | head -c 200
            echo "..."
        else
            echo "  $endpoint_name: ${#response} bytes"
        fi
        print_status "pass" "$ticker/$endpoint_name"
    else
        print_status "fail" "$ticker/$endpoint_name (HTTP $http_code)"
    fi
}

# Main test functions
test_health_endpoints() {
    echo ""
    echo "========================================================================="
    echo "HEALTH CHECKS"
    echo "========================================================================="
    
    # Main API health
    local response
    response=$(curl -s -w "\n%{http_code}" "$API/health" 2>/dev/null || echo "000")
    local http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "200" ]]; then
        print_status "pass" "Main API Health Check"
    else
        print_status "fail" "Main API Health Check (HTTP $http_code)"
    fi
    
    # Ollama health
    response=$(curl -s -w "\n%{http_code}" "$API/health/ollama" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    response=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" == "200" ]]; then
        if [[ "$RAW_OUTPUT" == true ]]; then
            echo "$response" | head -c 200
        fi
        print_status "pass" "Ollama Health Check"
    else
        print_status "fail" "Ollama Health Check (HTTP $http_code)"
    fi
}

test_data_endpoints() {
    echo ""
    echo "========================================================================="
    echo "DATA ENDPOINTS"
    echo "========================================================================="
    
    local endpoints=(
        "fundamentals:Fundamentals"
        "price-history:Price History"
        "analyst-targets:Analyst Targets"
        "calendar:Calendar"
        "income-stmt:Income Statement"
        "balance-sheet:Balance Sheet"
        "option-chain:Option Chain"
        "news:News"
    )
    
    for ticker in "${TICKER_ARRAY[@]}"; do
        echo ""
        echo "$ticker (8 endpoints):"
        for endpoint_pair in "${endpoints[@]}"; do
            IFS=':' read -r endpoint endpoint_name <<< "$endpoint_pair"
            test_endpoint "$ticker" "$endpoint" "$endpoint_name"
        done
    done
}

test_screening_endpoint() {
    echo ""
    echo "========================================================================="
    echo "SCREENING ENDPOINT"
    echo "========================================================================="
    
    local url="$API/api/screen-undervalued"
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    response=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" == "200" ]]; then
        local count=$(echo "$response" | grep -o '"' | wc -l)
        if [[ "$RAW_OUTPUT" == true ]]; then
            echo "$response" | head -c 200
            echo ""
        else
            echo "  Found ~$((count/4)) tickers"
        fi
        print_status "pass" "Screen Undervalued Endpoint"
    else
        print_status "fail" "Screen Undervalued Endpoint (HTTP $http_code)"
    fi
}

# Summary
print_summary() {
    echo ""
    echo "========================================================================="
    echo "TEST SUMMARY"
    echo "========================================================================="
    local total=$((PASSED + FAILED))
    local pass_rate=0
    if [[ $total -gt 0 ]]; then
        pass_rate=$((PASSED * 100 / total))
    fi
    
    echo "API: $API"
    echo "Tickers: ${TICKER_ARRAY[*]}"
    echo ""
    echo "Total: $total"
    echo -e "${GREEN}Passed: $PASSED${NC}"
    echo -e "${RED}Failed: $FAILED${NC}"
    echo "Pass Rate: ${pass_rate}%"
    echo "========================================================================="
    echo ""
}

# Main execution
main() {
    echo ""
    echo "========================================================================="
    echo "REMOTE API COMPREHENSIVE TEST SUITE"
    echo "========================================================================="
    
    [[ "$TEST_HEALTH" == true ]] && test_health_endpoints
    [[ "$TEST_DATA" == true ]] && test_data_endpoints
    [[ "$TEST_SCREENING" == true ]] && test_screening_endpoint
    
    print_summary
    
    return $([[ $FAILED -eq 0 ]] && echo 0 || echo 1)
}

main
