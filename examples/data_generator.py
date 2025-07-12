"""
Example data generator for MCP Backtest
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path


def generate_sample_crypto_data(
    symbol: str = "BTC/USD",
    days: int = 365,
    start_date: datetime = None,
    initial_price: float = 40000.0,
    volatility: float = 0.05
) -> pd.DataFrame:
    """Generate sample crypto data with realistic price movements"""
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    # Generate timestamps
    timestamps = pd.date_range(start=start_date, periods=days, freq='D')
    
    # Generate price data using geometric Brownian motion
    dt = 1/365  # daily timestep
    mu = 0.1  # annual drift
    sigma = volatility * np.sqrt(dt)
    
    # Generate random returns
    returns = np.random.normal(mu * dt, sigma, days)
    
    # Calculate cumulative prices
    prices = [initial_price]
    for i in range(1, days):
        prices.append(prices[-1] * np.exp(returns[i]))
    
    # Generate OHLCV data
    data = []
    for i, (timestamp, close_price) in enumerate(zip(timestamps, prices)):
        # Generate intraday price range
        daily_range = abs(np.random.normal(0, close_price * 0.02))
        
        # Generate OHLC
        if i == 0:
            open_price = close_price
        else:
            open_price = prices[i-1]
        
        high_price = max(open_price, close_price) + daily_range * np.random.random()
        low_price = min(open_price, close_price) - daily_range * np.random.random()
        
        # Generate volume (higher volume on larger price movements)
        volume = abs(np.random.normal(1000000, 500000)) * (1 + abs(returns[i]) * 10)
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 0)
        })
    
    return pd.DataFrame(data)


def generate_sample_stock_data(
    symbol: str = "AAPL",
    days: int = 252,
    start_date: datetime = None,
    initial_price: float = 150.0,
    volatility: float = 0.02
) -> pd.DataFrame:
    """Generate sample stock data"""
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    # Generate timestamps (exclude weekends)
    timestamps = pd.bdate_range(start=start_date, periods=days, freq='D')
    
    # Generate price data
    dt = 1/252  # business days per year
    mu = 0.08  # annual drift
    sigma = volatility * np.sqrt(dt)
    
    returns = np.random.normal(mu * dt, sigma, days)
    
    prices = [initial_price]
    for i in range(1, days):
        prices.append(prices[-1] * np.exp(returns[i]))
    
    # Generate OHLCV data
    data = []
    for i, (timestamp, close_price) in enumerate(zip(timestamps, prices)):
        daily_range = abs(np.random.normal(0, close_price * 0.015))
        
        if i == 0:
            open_price = close_price
        else:
            open_price = prices[i-1]
        
        high_price = max(open_price, close_price) + daily_range * np.random.random()
        low_price = min(open_price, close_price) - daily_range * np.random.random()
        
        volume = abs(np.random.normal(50000000, 20000000)) * (1 + abs(returns[i]) * 5)
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 0)
        })
    
    return pd.DataFrame(data)


def generate_sample_forex_data(
    symbol: str = "EUR/USD",
    days: int = 365,
    start_date: datetime = None,
    initial_price: float = 1.1000,
    volatility: float = 0.01
) -> pd.DataFrame:
    """Generate sample forex data"""
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    # Generate timestamps (forex trades 24/7)
    timestamps = pd.date_range(start=start_date, periods=days, freq='D')
    
    # Generate price data
    dt = 1/365
    mu = 0.02  # lower drift for forex
    sigma = volatility * np.sqrt(dt)
    
    returns = np.random.normal(mu * dt, sigma, days)
    
    prices = [initial_price]
    for i in range(1, days):
        prices.append(prices[-1] * np.exp(returns[i]))
    
    # Generate OHLCV data
    data = []
    for i, (timestamp, close_price) in enumerate(zip(timestamps, prices)):
        daily_range = abs(np.random.normal(0, close_price * 0.008))
        
        if i == 0:
            open_price = close_price
        else:
            open_price = prices[i-1]
        
        high_price = max(open_price, close_price) + daily_range * np.random.random()
        low_price = min(open_price, close_price) - daily_range * np.random.random()
        
        volume = abs(np.random.normal(1000000, 300000))
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 4),
            'high': round(high_price, 4),
            'low': round(low_price, 4),
            'close': round(close_price, 4),
            'volume': round(volume, 0)
        })
    
    return pd.DataFrame(data)


def create_sample_data_files():
    """Create sample data files for testing"""
    
    # Create data directory
    data_dir = Path("examples/data")
    data_dir.mkdir(exist_ok=True)
    
    # Generate crypto data
    crypto_data = generate_sample_crypto_data("BTC/USD", days=365)
    crypto_data.to_csv(data_dir / "btc_usd_sample.csv", index=False)
    
    # Save as JSON too
    crypto_json = {
        "symbol": "BTC/USD",
        "market_type": "crypto",
        "data": crypto_data.to_dict('records')
    }
    with open(data_dir / "btc_usd_sample.json", 'w') as f:
        json.dump(crypto_json, f, indent=2, default=str)
    
    # Generate stock data
    stock_data = generate_sample_stock_data("AAPL", days=252)
    stock_data.to_csv(data_dir / "aapl_sample.csv", index=False)
    
    # Save as JSON too
    stock_json = {
        "symbol": "AAPL",
        "market_type": "stock",
        "data": stock_data.to_dict('records')
    }
    with open(data_dir / "aapl_sample.json", 'w') as f:
        json.dump(stock_json, f, indent=2, default=str)
    
    # Generate forex data
    forex_data = generate_sample_forex_data("EUR/USD", days=365)
    forex_data.to_csv(data_dir / "eurusd_sample.csv", index=False)
    
    # Save as JSON too
    forex_json = {
        "symbol": "EUR/USD",
        "market_type": "forex",
        "data": forex_data.to_dict('records')
    }
    with open(data_dir / "eurusd_sample.json", 'w') as f:
        json.dump(forex_json, f, indent=2, default=str)
    
    print("Sample data files created:")
    print(f"  - {data_dir / 'btc_usd_sample.csv'}")
    print(f"  - {data_dir / 'btc_usd_sample.json'}")
    print(f"  - {data_dir / 'aapl_sample.csv'}")
    print(f"  - {data_dir / 'aapl_sample.json'}")
    print(f"  - {data_dir / 'eurusd_sample.csv'}")
    print(f"  - {data_dir / 'eurusd_sample.json'}")


if __name__ == "__main__":
    create_sample_data_files()