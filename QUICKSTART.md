# MCP Backtest - Quick Start Guide

## Overview

MCP Backtest is a sophisticated backtesting agent for financial markets that supports crypto, stock, and forex trading strategies. It integrates with multiple AI providers and can process data from various sources.

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/fathproject/mcp-backtest.git
cd mcp-backtest

# Install dependencies
pip install -e .
```

### 2. Basic Usage

```python
import asyncio
from mcp_backtest.client import BacktestClient

async def main():
    client = BacktestClient()
    
    # Load data from CSV
    data = await client.load_data_from_csv("data/btc_usd.csv", "crypto", "BTC/USD")
    
    # Run backtest
    result = await client.run_backtest(
        data=data,
        strategy="moving_average_crossover",
        market_type="crypto",
        llm_model="gpt-3.5-turbo",
        llm_provider="openai",
        initial_capital=10000
    )
    
    # Print results
    print(f"Total Return: {result.metrics.get('total_return', 0)*100:.2f}%")
    print(f"Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown: {result.metrics.get('max_drawdown', 0)*100:.2f}%")

asyncio.run(main())
```

### 3. MCP Server Usage

```bash
# Start the MCP server
mcp-backtest
```

Then use MCP tools:
- `run_backtest_csv` - Run backtest with CSV data
- `run_backtest_json` - Run backtest with JSON data
- `run_backtest_api` - Run backtest with API data
- `get_backtest_results` - Get results by test ID
- `list_strategies` - List available strategies
- `analyze_market_data` - Analyze market data using AI

### 4. Environment Setup

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
CLOUDFLARE_API_KEY=your_cloudflare_key
QWEN_API_KEY=your_qwen_key
DEEPSEEK_API_KEY=your_deepseek_key
```

## Features

### ✅ Data Input Support
- CSV files with OHLCV data
- JSON files with market data
- REST API endpoints
- Built-in data validation and preprocessing

### ✅ Trading Strategies
- Buy and Hold
- Moving Average Crossover
- RSI (Relative Strength Index)
- Mean Reversion (Bollinger Bands)
- Momentum Strategy
- Extensible strategy framework

### ✅ AI Integration
- OpenAI GPT models
- Google Gemini
- Anthropic Claude
- Cloudflare AI
- Qwen
- DeepSeek

### ✅ Market Support
- Cryptocurrency markets
- Stock markets
- Forex markets

### ✅ Backtesting Engine
- Realistic execution with slippage and commission
- Portfolio management
- Risk metrics calculation
- Performance analytics

### ✅ Result Analysis
- Comprehensive performance metrics
- Risk-adjusted returns
- Trade analysis
- Market comparison
- AI-powered insights

## Example Data Formats

### CSV Format
```csv
timestamp,open,high,low,close,volume
2024-01-01 00:00:00,100.0,102.0,99.0,101.0,1000
2024-01-01 01:00:00,101.0,103.0,100.0,102.0,1200
```

### JSON Format
```json
{
  "symbol": "BTC/USD",
  "market_type": "crypto",
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

## Running Examples

```bash
# Generate sample data
python examples/data_generator.py

# Run basic example
python examples/run_examples.py basic

# Run all examples
python examples/run_examples.py all

# Test without dependencies
python test_demo.py
```

## Architecture

```
mcp_backtest/
├── core/           # Core models and backtesting engine
├── data/           # Data handling and preprocessing
├── llm/            # AI provider integrations
├── strategies/     # Trading strategies
├── utils/          # Utility functions
├── client.py       # Client library
├── server.py       # MCP server
└── config.py       # Configuration management
```

## API Documentation

### Client Library

```python
from mcp_backtest.client import BacktestClient

client = BacktestClient()

# Load data
data = await client.load_data_from_csv("file.csv", "crypto", "BTC/USD")
data = await client.load_data_from_json("file.json", "stock", "AAPL")
data = await client.load_data_from_api("https://api.example.com/data", market_type="forex")

# Run backtest
result = await client.run_backtest(
    data=data,
    strategy="moving_average_crossover",
    market_type="crypto",
    llm_model="gpt-4",
    llm_provider="openai",
    strategy_params={"short_window": 10, "long_window": 30}
)

# Analyze data
analysis = await client.analyze_data(data, context="Market analysis")
strategy = await client.generate_strategy(data, requirements="Risk management")
```

### MCP Tools

Use with any MCP-compatible client:

```json
{
  "tool": "run_backtest_csv",
  "arguments": {
    "csv_path": "data/btc_usd.csv",
    "symbol": "BTC/USD",
    "market_type": "crypto",
    "strategy_name": "moving_average_crossover",
    "llm_provider": "openai",
    "llm_model": "gpt-3.5-turbo",
    "initial_capital": 10000
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Run tests: `python test_demo.py`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.