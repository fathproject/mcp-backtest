# MCP Backtest - Simplified Interface

## Overview

This MCP (Model Context Protocol) backtesting agent now provides a **simplified interface** where users only need to provide:

1. **Data source** (CSV file, JSON file, or API endpoint)
2. **Trading prompt** (description of desired trading strategy)

The MCP agent will automatically:
- Parse data intelligently (with or without headers)
- Detect market type and characteristics
- Generate appropriate trading strategy using AI
- Execute backtesting
- Provide comprehensive results

## Usage

### Simple Backtesting

```json
{
  "tool": "smart_backtest",
  "arguments": {
    "data_source": "path/to/your/data.csv",
    "trading_prompt": "I want a conservative long-term investment strategy"
  }
}
```

### Data Analysis

```json
{
  "tool": "analyze_data",
  "arguments": {
    "data_source": "path/to/your/data.csv",
    "analysis_prompt": "What are the key trends and patterns in this data?"
  }
}
```

## Features

### 🔍 Smart Data Parsing
- **Auto-header detection**: Works with or without column headers
- **Multiple formats**: CSV, JSON, and API endpoints
- **Intelligent column mapping**: Automatically maps to OHLCV format
- **Data validation**: Cleans and validates market data

### 🤖 AI-Powered Strategy Generation
- **Natural language prompts**: Describe your strategy in plain English
- **Market-aware**: Considers market type and characteristics
- **Multiple LLM providers**: OpenAI, Gemini, Claude, and more
- **Adaptive strategies**: Matches strategy to market conditions

### 📊 Comprehensive Results
- **Performance metrics**: Returns, Sharpe ratio, drawdown, etc.
- **AI analysis**: Detailed strategy explanation and market insights
- **Result matrix**: Complete backtesting results and statistics

## Examples

### Conservative Investment
```json
{
  "tool": "smart_backtest",
  "arguments": {
    "data_source": "btc_data.csv",
    "trading_prompt": "I want a conservative buy-and-hold strategy for long-term wealth building with minimal risk"
  }
}
```

### Aggressive Day Trading
```json
{
  "tool": "smart_backtest",
  "arguments": {
    "data_source": "stock_data.json",
    "trading_prompt": "I want an aggressive day trading strategy that captures short-term momentum with quick entries and exits"
  }
}
```

### Mean Reversion
```json
{
  "tool": "smart_backtest",
  "arguments": {
    "data_source": "https://api.example.com/ohlcv",
    "trading_prompt": "I want a mean reversion strategy that buys dips and sells peaks, suitable for sideways markets"
  }
}
```

## Data Format Support

### CSV Files
- With headers: `Date,Open,High,Low,Close,Volume`
- Without headers: Automatically detects OHLCV columns
- Flexible column names: `timestamp`, `price`, `vol`, etc.

### JSON Files
- Array of objects: `[{"date": "2023-01-01", "open": 100, ...}, ...]`
- Nested structures: `{"data": [{"ohlcv": [...]}]}`
- Flexible field names: Auto-mapped to standard format

### API Endpoints
- REST APIs returning JSON data
- Automatic structure detection
- Supports various response formats

## Configuration

Optional parameters for fine-tuning:

```json
{
  "tool": "smart_backtest",
  "arguments": {
    "data_source": "data.csv",
    "trading_prompt": "Conservative strategy",
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "initial_capital": 50000,
    "commission": 0.001
  }
}
```

## Benefits

1. **Simplified Interface**: No need to specify market type, symbol, or strategy parameters
2. **Intelligent Parsing**: Handles various data formats automatically
3. **AI Strategy Generation**: Creates custom strategies from natural language
4. **Comprehensive Analysis**: Provides detailed results and insights
5. **Flexible Data Sources**: Works with files, APIs, and various formats

This approach makes backtesting accessible to users regardless of their technical expertise or data format preferences.