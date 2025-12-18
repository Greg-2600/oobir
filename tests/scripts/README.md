# Test Scripts Consolidation Analysis

## Current Scripts in tests/scripts/

### 1. test_remote_api_comprehensive.sh ⭐ (MASTER)
- **Purpose**: Unified comprehensive test suite
- **Coverage**: Health checks + all 8 data endpoints × 5 tickers + screening
- **Features**:
  - Color-coded output
  - Pass/fail counting
  - Configurable API URL and tickers
  - Optional raw output mode
  - Selective test modes (--health-only, --data-only, etc)
- **Status**: NEW - Replaces multiple scripts below

### 2. test_curl_raw.sh (DEPRECATED - Superseded)
- **Purpose**: Raw output without jq filtering
- **Coverage**: All endpoints without piping
- **Issue**: Very verbose, repetitive, hard to parse
- **Replacement**: Use `test_remote_api_comprehensive.sh --raw`

### 3. test_curl_remote.sh (DEPRECATED - Superseded)
- **Purpose**: Test undervalued tickers with jq filtering
- **Coverage**: Health + first ticker only (F)
- **Issue**: Only tests one ticker, limited scope
- **Replacement**: Use `test_remote_api_comprehensive.sh`

### 4. test_curl_undervalued.sh (DEPRECATED - Superseded)
- **Purpose**: Test undervalued tickers
- **Coverage**: All 5 tickers, all 8 endpoints with jq
- **Issue**: Large output, uses piping which hides issues
- **Replacement**: Use `test_remote_api_comprehensive.sh`

### 5. test_curl_minimal.sh (DEPRECATED - Superseded)
- **Purpose**: Quick test of F, BBD, IREN, ITUB only
- **Coverage**: Fundamentals endpoint only
- **Issue**: Very limited scope
- **Replacement**: Use `test_remote_api_comprehensive.sh --tickers F,BBD,IREN,ITUB`

### 6. test_remaining_tickers.sh (DEPRECATED - Superseded)
- **Purpose**: Verify remaining tickers work
- **Coverage**: Fundamentals for F, BBD, IREN, ITUB
- **Issue**: Duplicate of test_curl_minimal.sh
- **Replacement**: Use `test_remote_api_comprehensive.sh`

### 7. verify_correct_routing.sh (DEPRECATED - Superseded)
- **Purpose**: Verify path parameter routing works
- **Coverage**: Fundamentals for 4 tickers
- **Issue**: Tests routing validation only
- **Replacement**: Use `test_remote_api_comprehensive.sh`

### 8. test_data_endpoints.sh (KEEP - Different Purpose)
- **Purpose**: Local testing with configurable host
- **Coverage**: All endpoints for any symbol
- **Features**: Graceful fallback (remote → localhost)
- **Use**: Local development testing
- **Status**: KEEP - Different use case than remote testing

### 9. test_ai_endpoints.sh (KEEP - Different Purpose)
- **Purpose**: Test AI analysis endpoints
- **Coverage**: LLM-based endpoints
- **Status**: KEEP - Separate from data endpoints
- **Todo**: Could be merged into comprehensive suite in future

### 10. screen_undervalued_recommendations.py (KEEP - Different Purpose)
- **Purpose**: Python screening utility
- **Status**: KEEP - Standalone utility for getting recommendations
- **Relationship**: Provides tickers tested by the shell scripts

## Consolidation Recommendations

### Phase 1: Immediate (Do Now)
✅ Created `test_remote_api_comprehensive.sh` as master test script
- [ ] Delete: test_curl_raw.sh
- [ ] Delete: test_curl_remote.sh  
- [ ] Delete: test_curl_undervalued.sh
- [ ] Delete: test_curl_minimal.sh
- [ ] Delete: test_remaining_tickers.sh
- [ ] Delete: verify_correct_routing.sh
- [ ] Keep: test_data_endpoints.sh
- [ ] Keep: test_ai_endpoints.sh
- [ ] Keep: screen_undervalued_recommendations.py

### Phase 2: Future Enhancements
- Merge test_ai_endpoints.sh into test_remote_api_comprehensive.sh
- Add AI endpoint testing with --ai flag
- Create unified test_local.sh for local development
- Consolidate all shell scripts into one modular framework

## Usage Guide

### For Remote Testing
```bash
# Full test suite
./tests/scripts/test_remote_api_comprehensive.sh

# Specific configuration
./tests/scripts/test_remote_api_comprehensive.sh \
  --api http://192.168.1.248:8000 \
  --tickers F,BBD,IREN,ITUB,VALE

# Health checks only
./tests/scripts/test_remote_api_comprehensive.sh --health-only

# Data endpoints only
./tests/scripts/test_remote_api_comprehensive.sh --data-only

# Screening only
./tests/scripts/test_remote_api_comprehensive.sh --screening-only

# Raw output (for debugging)
./tests/scripts/test_remote_api_comprehensive.sh --raw

# All options combined
./tests/scripts/test_remote_api_comprehensive.sh \
  --api http://remote.example.com:8000 \
  --tickers F,AAPL \
  --data-only \
  --raw
```

### For Local Testing
```bash
# Test localhost
./tests/scripts/test_data_endpoints.sh http://localhost:8000 F

# Test with fallback (tries remote, falls back to localhost)
./tests/scripts/test_data_endpoints.sh
```

### For AI Endpoints
```bash
./tests/scripts/test_ai_endpoints.sh
```

### For Recommendations
```bash
./tests/scripts/screen_undervalued_recommendations.py
```

## Summary

| Script | Purpose | Status | Keep |
|--------|---------|--------|------|
| test_remote_api_comprehensive.sh | Master remote test suite | NEW | ✅ |
| test_data_endpoints.sh | Local development testing | Working | ✅ |
| test_ai_endpoints.sh | AI endpoint testing | Working | ✅ |
| screen_undervalued_recommendations.py | Screening utility | Working | ✅ |
| test_curl_raw.sh | Raw output (legacy) | Superseded | ❌ |
| test_curl_remote.sh | Single ticker test (legacy) | Superseded | ❌ |
| test_curl_undervalued.sh | Multi-ticker test (legacy) | Superseded | ❌ |
| test_curl_minimal.sh | Limited test (legacy) | Superseded | ❌ |
| test_remaining_tickers.sh | Routing validation (legacy) | Superseded | ❌ |
| verify_correct_routing.sh | Routing check (legacy) | Superseded | ❌ |

**Result**: 4 active scripts, 6 deprecated scripts consolidated into 1 master script
