# News Sentiment Analysis Feature

**Added**: December 18, 2025  
**Branch**: `news_improvements`

## Overview

The News Sentiment Analysis feature automatically fetches recent news for a given stock ticker and uses AI (via Ollama/Llama model) to analyze whether the news sentiment is positive, negative, or neutral for investors. This provides a quick AI-driven assessment of market sentiment based on recent headlines.

## Features

- **Automated News Fetching**: Uses `yfinance` to retrieve recent news for any stock
- **Intelligent Summarization**: Extracts the top 5 news summaries for analysis
- **AI-Powered Analysis**: Leverages Ollama's Llama 3.2 model for sentiment classification
- **REST API Endpoint**: Easy integration via HTTP GET request
- **Error Handling**: Graceful handling of missing news or API failures
- **Comprehensive Logging**: Tracks all operations for debugging and monitoring

## Architecture

### Components

**1. Core Function: `flow.get_ai_news_sentiment(ticker)`**
- Located in: [flow.py](flow.py#L677)
- Purpose: Fetch news and analyze sentiment using AI
- Returns: String with sentiment analysis or None on error
- Model: `huihui_ai/llama3.2-abliterate:3b`

**2. API Endpoint: `/api/ai/news-sentiment/{symbol}`**
- Located in: [flow_api.py](flow_api.py#L402)
- Method: GET
- Returns: JSON response with sentiment analysis
- Status Codes:
  - `200`: Successful analysis
  - `503`: Ollama unavailable
  - `500`: Other errors

### Data Flow

```
User Request
    ↓
/api/ai/news-sentiment/{symbol} (FastAPI endpoint)
    ↓
flow.get_ai_news_sentiment(ticker)
    ↓
flow.get_news(ticker) [yfinance]
    ↓
Extract summaries (top 5 articles)
    ↓
flow.ensure_ollama() [connection check]
    ↓
flow._CHAT() [Ollama API call]
    ↓
Llama model analyzes sentiment
    ↓
Return sentiment analysis string
```

## Usage

### Via REST API

```bash
# Basic usage
curl http://192.168.1.248:8000/api/ai/news-sentiment/CHTR

# With pretty printing
curl -s http://192.168.1.248:8000/api/ai/news-sentiment/TSLA | jq

# With timeout
curl --max-time 30 http://192.168.1.248:8000/api/ai/news-sentiment/AAPL
```

### Example Response

```json
"The overall sentiment is positive for investors, as recent news summaries suggest that activist buzz, successful spin-offs, and insider buyouts are contributing to increased stock prices for Comcast and Charter Communications."
```

### Via Python

```python
import flow

# Ensure Ollama is running
flow.ensure_ollama()

# Get news sentiment
sentiment = flow.get_ai_news_sentiment('AAPL')
print(sentiment)
```

## Implementation Details

### Algorithm Steps

1. **Fetch News**: Use `yfinance` to get recent news articles for the ticker
2. **Extract Content**: Parse each article's content dictionary
3. **Collect Summaries**: Extract summary field from each article's content
4. **Limit to Top 5**: Use only the first 5 article summaries to keep prompts reasonable
5. **Format Prompt**: Create a structured prompt for the AI model
6. **Call Ollama**: Send request to Ollama's Llama 3.2 model
7. **Extract Response**: Parse the model's response message
8. **Return Result**: Return the sentiment analysis string

### Key Code Snippet

```python
def get_ai_news_sentiment(ticker):
    """Analyze news sentiment for a ticker using AI."""
    try:
        # Fetch news
        news = get_news(ticker)
        if not news:
            return "No news available for analysis."
        
        # Extract summaries
        summaries = []
        for article in news:
            content = article.get('content', {})
            summary = content.get('summary', '')
            if summary:
                summaries.append(summary)
        
        if not summaries:
            return "No news summaries available for analysis."
        
        # Combine top 5 articles
        combined_news = "\n".join(summaries[:5])
        
        # Get AI analysis
        ensure_ollama()
        response = _CHAT(
            model='huihui_ai/llama3.2-abliterate:3b',
            messages=[{
                'role': 'user',
                'content': (
                    'Based on the following recent news summaries, determine if the overall '
                    'sentiment is good or bad for investors. Respond in a single sentence '
                    'summarizing whether the news is positive, negative, or neutral for the stock. '
                    f'News summaries:\n{combined_news}'
                ),
            }]
        )
        
        sentiment = getattr(response, 'message', response).content
        return sentiment
        
    except Exception as exc:
        print(f"An error occurred while analyzing news sentiment: {exc}")
        return None
```

## Testing

### Unit Tests

Located in: [tests/test_news_sentiment.py](tests/test_news_sentiment.py)

Run tests:
```bash
python -m pytest tests/test_news_sentiment.py -v
```

**Test Coverage:**
- ✅ Valid news data processing
- ✅ No news available scenario
- ✅ No summaries in articles scenario
- ✅ Top 5 articles filtering
- ✅ Error handling
- ✅ Content extraction accuracy

### API Tests

Located in: [tests/test_api_news_sentiment.py](tests/test_api_news_sentiment.py)

Run tests:
```bash
python -m pytest tests/test_api_news_sentiment.py -v
```

**Test Coverage:**
- ✅ Endpoint success response (200)
- ✅ None result handling (503)
- ✅ Ollama connection errors (500)
- ✅ Multiple stock symbols
- ✅ Response format validation
- ✅ Case sensitivity handling
- ✅ Special characters in symbols (e.g., BRK.B)

### Manual Testing

```bash
# Test with various stocks
curl http://192.168.1.248:8000/api/ai/news-sentiment/AAPL
curl http://192.168.1.248:8000/api/ai/news-sentiment/MSFT
curl http://192.168.1.248:8000/api/ai/news-sentiment/CHTR
curl http://192.168.1.248:8000/api/ai/news-sentiment/TSLA

# Check response time
time curl -s http://192.168.1.248:8000/api/ai/news-sentiment/NVDA
```

## Configuration

### Environment Variables

- `OLLAMA_HOST`: Ollama service endpoint (default: `http://ollama:11434`)
- `OLLAMA_MODEL`: Model to use (hardcoded in function: `huihui_ai/llama3.2-abliterate:3b`)

### Model Configuration

- **Model**: `huihui_ai/llama3.2-abliterate:3b`
- **Provider**: Ollama (Docker container or remote)
- **Size**: ~3B parameters
- **Context Window**: 8K tokens

### Requirements

- yfinance: For news fetching
- ollama: For AI model interaction
- fastapi: For REST API
- uvicorn: For API server

## Performance Considerations

### Response Time

- Typical: 5-10 seconds per request
- Maximum timeout: 600 seconds (10 minutes) configured in API
- Factors affecting speed:
  - News availability (yfinance network call)
  - Ollama model load time
  - Model inference speed
  - Network latency

### Optimization Tips

1. **Batch Processing**: Process multiple tickers in parallel
2. **Caching**: Consider caching results for recent requests
3. **Rate Limiting**: Implement rate limiting to prevent overload
4. **Model Optimization**: Use smaller model variant if latency is critical

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 503 Service Unavailable | Ollama not running | Start Ollama container |
| Model not found (404) | Model not installed | Pull model: `docker exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b` |
| No news available | Stock has no recent news | Use different ticker or check yfinance |
| Timeout | Processing taking too long | Increase timeout or check system resources |

### Graceful Degradation

- Returns informative message if no news available
- Returns None with error logging if Ollama fails
- API returns 503 instead of crashing on Ollama errors
- Proper error propagation through stack

## Future Improvements

### Planned Enhancements

1. **Multiple Models**: Support different LLM models for sentiment analysis
2. **Sentiment Score**: Return numerical sentiment score (-1 to +1) in addition to text
3. **Time-based Filtering**: Allow filtering news by date range
4. **Sentiment Trends**: Track sentiment changes over time
5. **Sector Analysis**: Aggregate sentiment across sector
6. **News Source Weighting**: Weight sentiment based on news source credibility
7. **Caching Layer**: Redis cache for recent sentiment analyses
8. **Batch API**: Accept multiple tickers and return batch results

### Potential Features

- Real-time sentiment updates
- Historical sentiment tracking
- Sentiment-based trading signals
- Integration with portfolio management
- Webhook notifications on sentiment changes

## Related Functions

- `flow.get_news(ticker)`: Fetch raw news data
- `flow.ensure_ollama()`: Ensure Ollama connectivity
- `flow._CHAT()`: Call Ollama's chat API
- `flow.get_ai_action_recommendation()`: Related AI analysis

## Files Changed

### New Files
- [tests/test_news_sentiment.py](tests/test_news_sentiment.py) - Unit tests
- [tests/test_api_news_sentiment.py](tests/test_api_news_sentiment.py) - API tests
- [NEWS_SENTIMENT.md](NEWS_SENTIMENT.md) - This documentation

### Modified Files
- [flow.py](flow.py#L677) - Added `get_ai_news_sentiment()` function
- [flow_api.py](flow_api.py#L402) - Added `/api/ai/news-sentiment/{symbol}` endpoint
- [docker-compose.yml](docker-compose.yml) - Updated context size configuration
- [DOCS.md](DOCS.md) - Updated endpoint list and examples

## References

### Dependencies
- [yfinance](https://github.com/ranaroussi/yfinance) - Financial data
- [ollama-py](https://github.com/ollama/ollama-python) - Ollama client
- [FastAPI](https://fastapi.tiangolo.com/) - REST API framework

### Models
- [Llama 3.2](https://www.llama.com/) - Meta's open source LLM
- [huihui_ai/llama3.2-abliterate](https://huggingface.co/huihui/abliterate) - Optimized variant

### Related Documentation
- [DOCS.md](DOCS.md) - API documentation
- [README.md](README.md) - Quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review test files for usage examples
3. Check logs: `docker compose logs app`
4. Verify Ollama health: `curl http://localhost:11435/api/tags`

---

**Branch**: `news_improvements`  
**Status**: ✅ Implemented and tested  
**Date**: December 18, 2025
