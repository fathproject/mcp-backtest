# MetaAPI Live Trading Integration

The MCP Backtest agent now supports **real-time live trading** through MetaAPI integration. This allows you to execute AI-generated trading strategies on live forex and CFD markets.

## 🚀 Features

### Live Trading Capabilities
- **Real-time execution** of AI-generated strategies
- **MetaTrader 4/5 integration** through MetaAPI
- **Multi-symbol trading** support
- **Risk management** with position sizing and stop losses
- **Real-time monitoring** and performance tracking

### Trading Modes
- **Demo Mode**: Paper trading with real market data
- **Live Mode**: Real money trading (use with caution)
- **Paper Mode**: Simulation without broker connection

## 🔧 Setup

### 1. Get MetaAPI Account
1. Sign up at [MetaAPI.cloud](https://app.metaapi.cloud/)
2. Create a trading account (MT4/MT5)
3. Get your API key and account ID

### 2. Configure Environment
Add to your `.env` file:
```bash
# MetaAPI Configuration
METAAPI_API_KEY=your_metaapi_api_key_here
METAAPI_ACCOUNT_ID=your_metaapi_account_id_here
METAAPI_REGION=new-york  # or 'london', 'singapore'
METAAPI_PLATFORM=mt4  # or 'mt5'
```

### 3. Install Dependencies
```bash
pip install -e .
```

## 📊 MCP Tools for Live Trading

### 1. Start Live Trading
```json
{
  "tool": "start_live_trading",
  "arguments": {
    "symbols": ["EURUSD", "GBPUSD", "AUDUSD"],
    "trading_prompt": "I want a conservative scalping strategy for EUR/USD that trades small moves with tight stops",
    "mode": "demo",
    "llm_provider": "openai",
    "llm_model": "gpt-4"
  }
}
```

### 2. Monitor Trading Status
```json
{
  "tool": "get_trading_status",
  "arguments": {
    "session_id": "your_session_id"
  }
}
```

### 3. Stop Trading
```json
{
  "tool": "stop_live_trading",
  "arguments": {
    "session_id": "your_session_id"
  }
}
```

### 4. Check Account Info
```json
{
  "tool": "get_account_info",
  "arguments": {}
}
```

## 💡 Usage Examples

### Conservative Long-term Strategy
```json
{
  "tool": "start_live_trading",
  "arguments": {
    "symbols": ["EURUSD", "GBPUSD"],
    "trading_prompt": "Conservative long-term trend following strategy with 1:2 risk-reward ratio. Trade daily timeframe with moving average crossovers.",
    "mode": "demo"
  }
}
```

### Scalping Strategy
```json
{
  "tool": "start_live_trading",
  "arguments": {
    "symbols": ["EURUSD"],
    "trading_prompt": "Scalping strategy for EUR/USD using 5-minute charts. Quick entries and exits with 10-pip stops and 20-pip targets.",
    "mode": "demo"
  }
}
```

### Multi-Currency Strategy
```json
{
  "tool": "start_live_trading",
  "arguments": {
    "symbols": ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY"],
    "trading_prompt": "Diversified currency portfolio strategy. Trade major pairs with momentum indicators and correlation analysis.",
    "mode": "demo"
  }
}
```

## ⚠️ Risk Management

### Built-in Risk Controls
- **Position sizing**: Automatic calculation based on account equity
- **Stop losses**: Automatically set for all positions
- **Daily loss limit**: Trading stops if daily loss exceeds 5%
- **Maximum positions**: Limits concurrent open positions
- **Risk per trade**: Default 2% of account equity

### Trading Modes
- **Always start with DEMO mode** for testing
- **Never risk more than you can afford to lose**
- **Monitor your trades regularly**
- **Use appropriate position sizing**

## 📈 Strategy Generation

The AI analyzes your trading prompt and generates appropriate strategies:

### Prompt Examples
- "Conservative strategy for retirement account"
- "Aggressive scalping for quick profits"
- "Trend following with momentum indicators"
- "Mean reversion strategy for range-bound markets"
- "Breakout strategy for volatile sessions"

### AI Considerations
- **Market conditions**: Current volatility and trends
- **Risk tolerance**: Based on your prompt language
- **Timeframe**: Inferred from strategy description
- **Indicators**: Selected based on strategy type
- **Risk management**: Automatically included

## 🔍 Monitoring and Analytics

### Real-time Monitoring
- **Live P&L tracking**
- **Position monitoring**
- **Signal generation status**
- **Risk metrics**
- **Performance analytics**

### Performance Metrics
- **Daily P&L**
- **Win rate**
- **Risk-reward ratio**
- **Maximum drawdown**
- **Sharpe ratio**

## 🛠️ Technical Details

### MetaAPI Integration
- **REST API**: For account management and trading
- **WebSocket**: For real-time data and events
- **Error handling**: Robust error management
- **Reconnection**: Automatic reconnection logic

### Strategy Execution
- **Signal generation**: 1-minute intervals
- **Order management**: Automatic SL/TP setting
- **Position tracking**: Real-time position updates
- **Risk checks**: Continuous risk monitoring

## 📚 Best Practices

### Getting Started
1. **Start with demo mode** to test strategies
2. **Use small position sizes** initially
3. **Monitor performance** closely
4. **Adjust strategies** based on results

### Risk Management
1. **Set clear risk limits** before trading
2. **Use stop losses** on all positions
3. **Diversify across instruments**
4. **Don't overtrade**

### Strategy Development
1. **Test thoroughly** in demo mode
2. **Start with simple strategies**
3. **Gradually increase complexity**
4. **Document what works**

## 🔗 Integration with Client

```python
from mcp_backtest.client import BacktestClient

async def start_live_trading():
    client = BacktestClient()
    
    # Start live trading
    result = await client.start_live_trading(
        symbols=["EURUSD", "GBPUSD"],
        trading_prompt="Conservative trend following strategy",
        mode="demo"
    )
    
    session_id = result["session_id"]
    
    # Monitor status
    status = await client.get_trading_status(session_id)
    print(f"Trading Status: {status}")
    
    # Stop when done
    await client.stop_live_trading(session_id)
```

## 🆘 Troubleshooting

### Common Issues
1. **API Key Invalid**: Check your MetaAPI credentials
2. **Account Not Connected**: Ensure MT4/MT5 is running
3. **Insufficient Margin**: Check account balance
4. **Symbol Not Found**: Verify symbol names with broker

### Support
- Check MetaAPI documentation
- Review server logs for errors
- Test with demo account first
- Contact support if needed

## ⚡ Quick Start

1. Set up MetaAPI account
2. Configure environment variables
3. Start with demo mode:
```json
{
  "tool": "start_live_trading",
  "arguments": {
    "symbols": ["EURUSD"],
    "trading_prompt": "Simple buy and hold strategy",
    "mode": "demo"
  }
}
```

**Remember**: Always test thoroughly in demo mode before live trading!