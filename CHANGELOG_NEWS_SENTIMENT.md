# Changelog - News Sentiment Analysis Feature

## [Unreleased] - news_improvements branch

### Added

#### Core Functionality
- **News Sentiment Analysis Function** (`flow.get_ai_news_sentiment()`)
  - Fetches recent news for a stock ticker using yfinance
  - Extracts top 5 news summaries
  - Analyzes sentiment using Ollama LLM model
  - Returns single-sentence sentiment assessment
  - Handles edge cases (no news, no summaries, errors)

#### REST API Endpoint
- **`GET /api/ai/news-sentiment/{symbol}`**
  - Accepts stock ticker symbol
  - Returns AI-analyzed sentiment as JSON string
  - Proper error handling (503 for Ollama unavailable, 500 for other errors)
  - Comprehensive logging of requests and responses

#### Testing
- **Unit Tests** (`tests/test_news_sentiment.py`)
  - Test valid news analysis
  - Test no news available scenario
  - Test no summaries edge case
  - Test exception handling
  - Test top 5 articles limit
  - Test positive/negative/mixed sentiment responses

- **API Tests** (`tests/test_api_news_sentiment.py`)
  - Test endpoint existence
  - Test successful responses
  - Test error scenarios
  - Test logging functionality

#### Documentation
- **NEWS_SENTIMENT.md**: Comprehensive feature documentation
  - API endpoint specification
  - Python API usage examples
  - How it works (data flow)
  - Model configuration
  - Error handling guide
  - Testing instructions
  - Integration examples
  - Troubleshooting guide

- **DOCS.md Updates**
  - Added `get_ai_news_sentiment` to AI Functions list
  - Added `/api/ai/news-sentiment/{symbol}` to API endpoints
  - Updated endpoint count from 23 to 24
  - Added example curl command for news sentiment
  - Updated total AI Functions count from 8 to 9

### Changed

#### flow.py
- Added `get_ai_news_sentiment(ticker)` function (line 677)
  - Uses existing `get_news()` for news retrieval
  - Uses `ensure_ollama()` for LLM connection
  - Uses `_CHAT()` for sentiment analysis
  - Follows established error handling patterns

#### flow_api.py
- Added `/api/ai/news-sentiment/{symbol}` endpoint (line 402)
  - Follows existing endpoint patterns
  - Includes proper logging
  - Includes error handling for None responses
  - Returns JSONResponse with sentiment analysis

### Technical Details

**Model Used**: `huihui_ai/llama3.2-abliterate:3b`
- Model Size: ~3B parameters
- Download Size: 2.2 GB
- Location: Ollama container

**Request Timeout**: 600 seconds (10 minutes)
- Allows time for large news summaries
- Aligns with other AI analysis endpoints

**Error Handling**:
- No news: Returns "No news available for analysis."
- No summaries: Returns "No news summaries available for analysis."
- Ollama error: Returns None, logs error
- Exception: Returns None with error logging

### Dependencies

No new external dependencies required. Uses existing:
- `yfinance` for news retrieval
- `ollama` for LLM integration
- `fastapi` for REST endpoint
- `requests` for logging/monitoring

### Testing Coverage

- 7 unit tests for sentiment analysis function
- 8 tests for API endpoint
- Tests cover: happy path, edge cases, errors, logging
- Mock-based testing for Ollama dependency

### Files Modified

1. `flow.py`
   - Added: `get_ai_news_sentiment()` function
   
2. `flow_api.py`
   - Added: `/api/ai/news-sentiment/{symbol}` endpoint

3. `tests/test_news_sentiment.py`
   - Enhanced with comprehensive unit tests
   
4. `tests/test_api_news_sentiment.py`
   - Enhanced with comprehensive API tests

5. `DOCS.md`
   - Updated AI Functions count (8→9)
   - Updated endpoint count (23→24)
   - Added news sentiment to documentation

### Documentation Added

1. `NEWS_SENTIMENT.md` - Feature documentation
2. Updated `DOCS.md` - Integration into main docs

### Backward Compatibility

✅ **Fully backward compatible**
- No changes to existing functions
- No changes to existing endpoints
- New endpoint added without affecting others
- Existing tests unchanged

### Future Enhancements

Potential improvements for future versions:
- Sentiment confidence scoring (0.0-1.0)
- Entity extraction (company names, events)
- Sentiment trend analysis over time
- Custom sentiment categories
- Multi-language support
- Caching of recent analyses
- Streaming responses for long analyses

### Validation

All changes validated:
- ✅ Endpoint responds without 404 errors
- ✅ Model downloads and loads correctly
- ✅ Sentiment analysis returns valid responses
- ✅ Error handling works for edge cases
- ✅ Tests pass with mocked Ollama
- ✅ Documentation complete and accurate
- ✅ No breaking changes to existing API
