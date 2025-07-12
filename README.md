# MCP Backtest

A sophisticated MCP (Model Context Protocol) backtesting agent for financial markets supporting crypto, stock, and forex trading strategies with **live trading capabilities**.

## 🚀 Features

### Core Capabilities
- **Multi-format Data Input**: Support for CSV, JSON, and REST API data sources
- **Multi-market Support**: Crypto, stock, and forex markets
- **AI-Powered Analysis**: Integration with multiple LLM providers (ChatGPT, Gemini, Cloudflare AI, Claude, Qwen, DeepSeek)
- **Strategy Execution**: Execute and backtest trading strategies
- **Comprehensive Results**: Generate detailed result matrices and performance metrics

### 🆕 Live Trading Integration
- **MetaAPI Integration**: Real-time trading with MetaTrader 4/5
- **Auto Strategy Generation**: AI creates strategies from natural language prompts
- **Risk Management**: Built-in position sizing and stop losses
- **Multi-mode Support**: Demo, live, and paper trading modes
- **Real-time Monitoring**: Live performance tracking and analytics

## 📦 Installation

```bash
pip install -e .
```

## 🔧 Setup

### 1. Basic Configuration
Create a `.env` file with your API keys:

```env
# AI Providers
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
CLOUDFLARE_API_KEY=your_cloudflare_key
QWEN_API_KEY=your_qwen_key
DEEPSEEK_API_KEY=your_deepseek_key

# MetaAPI for Live Trading
METAAPI_API_KEY=your_metaapi_key
METAAPI_ACCOUNT_ID=your_metaapi_account_id
```

### 2. Start MCP Server
```bash
mcp-backtest
```

## 💡 Usage Examples

### Smart Backtesting (Simplified Interface)
```json
{
  "tool": "smart_backtest",
  "arguments": {
    "data_source": "btc_data.csv",
    "trading_prompt": "I want a conservative long-term investment strategy"
  }
}
```

### Live Trading with MetaAPI
```json
{
  "tool": "start_live_trading",
  "arguments": {
    "symbols": ["EURUSD", "GBPUSD"],
    "trading_prompt": "Scalping strategy with tight stops and quick profits",
    "mode": "demo"
  }
}
```

### Data Analysis
```json
{
  "tool": "analyze_data",
  "arguments": {
    "data_source": "market_data.json",
    "analysis_prompt": "Identify trends and potential trading opportunities"
  }
}
```

## 🔗 Client Library Usage

```python
from mcp_backtest.client import BacktestClient

# Initialize client
client = BacktestClient()

# Smart backtesting
result = await client.smart_backtest(
    data_source="btc_data.csv",
    trading_prompt="Conservative buy and hold strategy"
)

# Live trading
session_id = await client.start_live_trading(
    symbols=["EURUSD"],
    trading_prompt="Trend following strategy",
    mode="demo"
)

# Monitor trading
status = await client.get_trading_status(session_id)
```

# Or from JSON
data = client.load_data_from_json("path/to/your/data.json")

# Or from REST API
data = client.load_data_from_api("https://api.example.com/data")

# Run backtest with strategy
results = client.run_backtest(
    data=data,
    strategy="buy_and_hold",
    market_type="crypto",
    llm_model="gpt-4"
)

# Get result matrix
matrix = results.get_result_matrix()
```

## API Endpoints

- `POST /backtest/csv` - Upload CSV data for backtesting
- `POST /backtest/json` - Upload JSON data for backtesting
- `POST /backtest/api` - Connect to external API for data
- `GET /strategies` - List available strategies
- `GET /models` - List available LLM models
- `GET /results/{test_id}` - Get backtest results

## Data Format

### CSV Format
```csv
timestamp,open,high,low,close,volume
2024-01-01 00:00:00,100.0,102.0,99.0,101.0,1000
```

### JSON Format
```json
{
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "open": 100.0,
      "high": 102.0,
      "low": 99.0,
      "close": 101.0,
      "volume": 1000
    }
  ]
}
```

## License

MIT