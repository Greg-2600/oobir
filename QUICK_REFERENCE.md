# OOBIR Quick Reference Guide

## 🚀 Quick Start (5 minutes)

### Docker (Recommended)
```bash
docker compose up -d
# Web UI: http://localhost:8081
# API Docs: http://localhost:8000/docs
```

### Local Development
```bash
# Terminal 1: API
python flow_api.py
# API runs on http://localhost:8000

# Terminal 2: Web UI
cd web && python -m http.server 8081
# Web UI runs on http://localhost:8081
```

## 📊 Web UI Usage

1. **Search**: Enter ticker symbol (e.g., AAPL, MSFT, TSLA)
2. **View Data**: Automatically loads 6 data sources
3. **Analyze Chart**: Interactive candlestick chart with technical indicators
4. **AI Analysis**: Click buttons to get AI recommendations, technical analysis, sentiment

## 🧪 Testing

```bash
# All tests (66 total)
pytest tests/ -v

# Quick test
pytest tests/test_web_ui_integration.py -v

# Docker test
docker compose exec app pytest tests/ -v
```

## 📁 Project Structure

```
oobir/
├── flow.py              # Business logic (CLI interface)
├── flow_api.py          # REST API (FastAPI)
├── web/                 # Web UI (HTML/CSS/JS)
│   ├── index.html       # Main interface
│   ├── app.js           # Frontend logic
│   ├── styles.css       # Styling
│   └── config.js        # Configuration
├── tests/               # Test suite (66 tests)
├── README.md            # Main documentation
├── WEB_UI_GUIDE.md      # Web UI development
├── TESTING.md           # Testing guide
├── CHANGELOG.md         # Version history
└── docker-compose.yml   # Container orchestration
```

## 🔌 API Endpoints (24 total)

### Health Checks
- `GET /health` - App health
- `GET /health/ollama` - LLM service health

### Data Endpoints (13)
- `GET /api/fundamentals/{symbol}` - Company metrics
- `GET /api/price-history/{symbol}` - 120+ days OHLCV
- `GET /api/analyst-targets/{symbol}` - Price targets
- `GET /api/calendar/{symbol}` - Earnings events
- `GET /api/balance-sheet/{symbol}` - Balance sheet
- `GET /api/income-stmt/{symbol}` - Income statement
- `GET /api/option-chain/{symbol}` - Options chain
- `GET /api/news/{symbol}` - News articles
- `GET /api/screen-undervalued` - Stock screener
- (+ 4 more alternative data endpoints)

### AI Endpoints (9)
- `GET /api/ai/action-recommendation/{symbol}` - Buy/sell/hold
- `GET /api/ai/technical-analysis/{symbol}` - Technical patterns
- `GET /api/ai/news-sentiment/{symbol}` - Sentiment analysis
- `GET /api/ai/fundamental-analysis/{symbol}` - Fundamentals
- `GET /api/ai/balance-sheet-analysis/{symbol}` - Balance sheet
- `GET /api/ai/income-stmt-analysis/{symbol}` - Income statement
- (+ 3 more recommendation formats)

## 🛠️ Configuration

### Web UI API URL
Edit `web/config.js`:
```javascript
const API_BASE_URL = 'http://192.168.1.248:8000'; // Your API server
```

### Docker Environment
Edit `docker-compose.yml`:
```yaml
environment:
  OLLAMA_HOST: http://ollama:11434
  # Add custom environment variables here
```

### API Port
```bash
# Use different port if 8000 is taken
docker compose up -d -p 8001:8000
```

## 📊 Technical Indicators (Web UI)

### Available Indicators
- **SMA 20** (Blue): 20-period simple moving average
- **SMA 50** (Orange): 50-period simple moving average
- **Bollinger Bands** (Purple): 20-period ±2 standard deviations

### Chart Features
- Green candles: Price closed higher than open
- Red candles: Price closed lower than open
- Wicks: Show high and low prices
- Hover: See OHLC data for each day

## 🧠 AI Models

### Ollama Integration
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Download model (if not present)
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b

# List available models
docker compose exec ollama ollama list
```

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Overview, features, quick start |
| `WEB_UI_GUIDE.md` | Web UI architecture and customization |
| `TESTING.md` | Test suite documentation |
| `CHANGELOG.md` | Version history and changes |
| `DOCUMENTATION_UPDATE_SUMMARY.md` | Summary of recent updates |

## 🐛 Troubleshooting

### Web UI Not Loading
```bash
# Check API is running
curl http://localhost:8000/health

# Check CORS is enabled
curl -H "Origin: http://localhost:8081" http://localhost:8000/api/fundamentals/AAPL

# Check Web UI files are served
curl http://localhost:8081/index.html
```

### Chart Not Rendering
- Check browser console (F12) for errors
- Verify price-history data has Date, Open, High, Low, Close
- Check for JavaScript syntax errors in app.js

### AI Endpoints Slow
- Verify Ollama service is running: `curl http://localhost:11434/api/tags`
- Check model is downloaded: `docker compose exec ollama ollama list`
- May take 10-30 seconds for LLM to generate responses

### Tests Failing
```bash
# Run with verbose output
pytest tests/ -vv --tb=long

# Run specific test
pytest tests/test_web_ui_integration.py::TestWebUIDataEndpoints -v

# Check Python environment
python --version  # Should be 3.11+
```

## 🚢 Deployment

### Remote Server
```bash
# Deploy with script
./scripts/deploy_remote.sh user@hostname ~/deployment_path

# Manual deployment
ssh user@hostname
git clone https://github.com/Greg-2600/oobir.git
cd oobir
docker compose up -d --build
docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b
```

### Verify Deployment
```bash
# Health checks
curl http://remote-server:8000/health
curl http://remote-server:8000/health/ollama

# API test
curl http://remote-server:8000/api/fundamentals/AAPL

# Web UI
open http://remote-server:8081
```

## 🔑 Key Concepts

### On-Demand AI Loading
- AI analysis buttons only load when clicked
- Prevents slow page loads
- Reduces unnecessary API calls

### Technical Indicators
- **SMA**: Shows trend direction
- **Bollinger Bands**: Show volatility levels
- All calculated client-side in Web UI

### Response Formats
- All APIs return JSON
- Web UI handles date-keyed and flat objects
- Errors return proper HTTP status codes

## 📱 Supported Browsers

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 🔗 Useful Links

- [FastAPI Docs](http://localhost:8000/docs)
- [yfinance Documentation](https://yfinance.readthedocs.io/)
- [Ollama Models](https://ollama.ai/library)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## 💡 Common Tasks

### Add a New Stock to Web UI
1. Search for ticker in Web UI
2. All data loads automatically
3. Chart, fundamentals, and AI analysis appear

### Customize Chart Colors
1. Edit `web/app.js`
2. Find `renderPriceHistory()` function
3. Change color hex codes
4. Reload Web UI (Ctrl+Shift+R for hard refresh)

### Monitor API Performance
```bash
# Check response times
time curl http://localhost:8000/api/fundamentals/AAPL

# Check all endpoints
for endpoint in fundamentals price-history analyst-targets calendar balance-sheet income-stmt; do
  echo "Testing $endpoint..."
  time curl http://localhost:8000/api/$endpoint/AAPL > /dev/null
done
```

### Debug JavaScript Issues
1. Open browser DevTools (F12)
2. Go to Console tab
3. Check for errors or warnings
4. Network tab shows API requests
5. Elements tab shows DOM structure

## 📞 Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: See README.md, WEB_UI_GUIDE.md, TESTING.md
- **Logs**: `docker compose logs -f app` (Docker)
- **Tests**: `pytest tests/ -v` (Verify functionality)

---

**Last Updated**: December 19, 2025  
**Version**: 1.1.0  
**Status**: Production Ready
