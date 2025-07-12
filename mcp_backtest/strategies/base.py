"""
Trading strategies for backtesting
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from abc import ABC, abstractmethod

from ..core.models import MarketData, TradeSignal, StrategyConfig


class BaseStrategy(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.strategy_name
        self.parameters = config.parameters
        self.risk_management = config.risk_management
    
    @abstractmethod
    async def generate_signals(self, market_data: MarketData) -> List[TradeSignal]:
        """Generate trading signals based on market data"""
        pass
    
    def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Calculate position size based on confidence and risk management"""
        base_size = self.parameters.get('position_size', 0.1)  # 10% of capital by default
        
        # Adjust based on confidence
        if confidence > 0.8:
            size_multiplier = 1.5
        elif confidence > 0.6:
            size_multiplier = 1.0
        else:
            size_multiplier = 0.5
        
        # Apply risk management
        max_position = self.risk_management.get('max_position_size', 0.2)
        
        return min(base_size * size_multiplier, max_position)


class BuyAndHoldStrategy(BaseStrategy):
    """Simple buy and hold strategy"""
    
    async def generate_signals(self, market_data: MarketData) -> List[TradeSignal]:
        """Generate buy and hold signals"""
        signals = []
        
        if not market_data.data:
            return signals
        
        # Buy at the beginning
        first_price = market_data.data[0]
        buy_signal = TradeSignal(
            timestamp=first_price.timestamp,
            action='buy',
            quantity=0,  # Will be calculated based on available capital
            price=first_price.close,
            confidence=1.0,
            reasoning="Buy and hold strategy - initial purchase"
        )
        signals.append(buy_signal)
        
        # Sell at the end
        last_price = market_data.data[-1]
        sell_signal = TradeSignal(
            timestamp=last_price.timestamp,
            action='sell',
            quantity=0,  # Will sell entire position
            price=last_price.close,
            confidence=1.0,
            reasoning="Buy and hold strategy - final sale"
        )
        signals.append(sell_signal)
        
        return signals


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Moving average crossover strategy"""
    
    async def generate_signals(self, market_data: MarketData) -> List[TradeSignal]:
        """Generate signals based on moving average crossover"""
        signals = []
        
        if not market_data.data:
            return signals
        
        # Get parameters
        short_window = self.parameters.get('short_window', 10)
        long_window = self.parameters.get('long_window', 30)
        
        # Convert to DataFrame for easier calculation
        df = pd.DataFrame([{
            'timestamp': price.timestamp,
            'close': price.close,
            'volume': price.volume
        } for price in market_data.data])
        
        if len(df) < long_window:
            return signals  # Not enough data
        
        # Calculate moving averages
        df['short_ma'] = df['close'].rolling(window=short_window).mean()
        df['long_ma'] = df['close'].rolling(window=long_window).mean()
        
        # Generate signals
        position = 0  # 0 = no position, 1 = long
        
        for i in range(long_window, len(df)):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Check for crossover
            if (prev_row['short_ma'] <= prev_row['long_ma'] and 
                current_row['short_ma'] > current_row['long_ma'] and 
                position == 0):
                # Golden cross - buy signal
                confidence = min(0.8, abs(current_row['short_ma'] - current_row['long_ma']) / current_row['long_ma'])
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='buy',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=f"Golden cross: Short MA ({current_row['short_ma']:.2f}) crossed above Long MA ({current_row['long_ma']:.2f})"
                )
                signals.append(signal)
                position = 1
                
            elif (prev_row['short_ma'] >= prev_row['long_ma'] and 
                  current_row['short_ma'] < current_row['long_ma'] and 
                  position == 1):
                # Death cross - sell signal
                confidence = min(0.8, abs(current_row['short_ma'] - current_row['long_ma']) / current_row['long_ma'])
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='sell',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=f"Death cross: Short MA ({current_row['short_ma']:.2f}) crossed below Long MA ({current_row['long_ma']:.2f})"
                )
                signals.append(signal)
                position = 0
        
        return signals


class RSIStrategy(BaseStrategy):
    """RSI (Relative Strength Index) strategy"""
    
    async def generate_signals(self, market_data: MarketData) -> List[TradeSignal]:
        """Generate signals based on RSI"""
        signals = []
        
        if not market_data.data:
            return signals
        
        # Get parameters
        rsi_period = self.parameters.get('rsi_period', 14)
        oversold_level = self.parameters.get('oversold_level', 30)
        overbought_level = self.parameters.get('overbought_level', 70)
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': price.timestamp,
            'close': price.close,
            'volume': price.volume
        } for price in market_data.data])
        
        if len(df) < rsi_period + 1:
            return signals
        
        # Calculate RSI
        df['price_change'] = df['close'].diff()
        df['gain'] = df['price_change'].where(df['price_change'] > 0, 0)
        df['loss'] = -df['price_change'].where(df['price_change'] < 0, 0)
        
        df['avg_gain'] = df['gain'].rolling(window=rsi_period).mean()
        df['avg_loss'] = df['loss'].rolling(window=rsi_period).mean()
        
        df['rs'] = df['avg_gain'] / df['avg_loss']
        df['rsi'] = 100 - (100 / (1 + df['rs']))
        
        # Generate signals
        position = 0  # 0 = no position, 1 = long
        
        for i in range(rsi_period, len(df)):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Buy signal - RSI crosses above oversold level
            if (prev_row['rsi'] <= oversold_level and 
                current_row['rsi'] > oversold_level and 
                position == 0):
                
                confidence = min(0.9, (oversold_level - prev_row['rsi']) / oversold_level)
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='buy',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=f"RSI oversold recovery: RSI {current_row['rsi']:.2f} crossed above {oversold_level}"
                )
                signals.append(signal)
                position = 1
            
            # Sell signal - RSI crosses below overbought level
            elif (prev_row['rsi'] >= overbought_level and 
                  current_row['rsi'] < overbought_level and 
                  position == 1):
                
                confidence = min(0.9, (prev_row['rsi'] - overbought_level) / (100 - overbought_level))
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='sell',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=f"RSI overbought correction: RSI {current_row['rsi']:.2f} crossed below {overbought_level}"
                )
                signals.append(signal)
                position = 0
        
        return signals


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy based on Bollinger Bands"""
    
    async def generate_signals(self, market_data: MarketData) -> List[TradeSignal]:
        """Generate signals based on mean reversion"""
        signals = []
        
        if not market_data.data:
            return signals
        
        # Get parameters
        window = self.parameters.get('window', 20)
        std_dev = self.parameters.get('std_dev', 2)
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': price.timestamp,
            'close': price.close,
            'volume': price.volume
        } for price in market_data.data])
        
        if len(df) < window:
            return signals
        
        # Calculate Bollinger Bands
        df['sma'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        df['upper_band'] = df['sma'] + (df['std'] * std_dev)
        df['lower_band'] = df['sma'] - (df['std'] * std_dev)
        
        # Generate signals
        position = 0  # 0 = no position, 1 = long
        
        for i in range(window, len(df)):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Buy signal - price touches lower band
            if (current_row['close'] <= current_row['lower_band'] and 
                prev_row['close'] > prev_row['lower_band'] and 
                position == 0):
                
                # Calculate confidence based on how far below the band
                distance_ratio = (current_row['lower_band'] - current_row['close']) / current_row['std']
                confidence = min(0.9, 0.5 + distance_ratio * 0.4)
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='buy',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=f"Mean reversion buy: Price {current_row['close']:.2f} touched lower band {current_row['lower_band']:.2f}"
                )
                signals.append(signal)
                position = 1
            
            # Sell signal - price touches upper band or returns to mean
            elif position == 1 and (
                (current_row['close'] >= current_row['upper_band'] and 
                 prev_row['close'] < prev_row['upper_band']) or
                (current_row['close'] >= current_row['sma'] and 
                 prev_row['close'] < prev_row['sma'])
            ):
                
                if current_row['close'] >= current_row['upper_band']:
                    confidence = 0.8
                    reason = f"Mean reversion sell: Price {current_row['close']:.2f} reached upper band {current_row['upper_band']:.2f}"
                else:
                    confidence = 0.6
                    reason = f"Mean reversion sell: Price {current_row['close']:.2f} returned to mean {current_row['sma']:.2f}"
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='sell',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=reason
                )
                signals.append(signal)
                position = 0
        
        return signals


class MomentumStrategy(BaseStrategy):
    """Momentum strategy based on price momentum"""
    
    async def generate_signals(self, market_data: MarketData) -> List[TradeSignal]:
        """Generate signals based on momentum"""
        signals = []
        
        if not market_data.data:
            return signals
        
        # Get parameters
        lookback_period = self.parameters.get('lookback_period', 10)
        momentum_threshold = self.parameters.get('momentum_threshold', 0.02)  # 2%
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': price.timestamp,
            'close': price.close,
            'volume': price.volume
        } for price in market_data.data])
        
        if len(df) < lookback_period:
            return signals
        
        # Calculate momentum
        df['momentum'] = df['close'].pct_change(periods=lookback_period)
        
        # Generate signals
        position = 0  # 0 = no position, 1 = long
        
        for i in range(lookback_period, len(df)):
            current_row = df.iloc[i]
            
            # Buy signal - strong positive momentum
            if (current_row['momentum'] > momentum_threshold and position == 0):
                confidence = min(0.9, current_row['momentum'] / (momentum_threshold * 2))
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='buy',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=f"Momentum buy: {current_row['momentum']:.2%} momentum over {lookback_period} periods"
                )
                signals.append(signal)
                position = 1
            
            # Sell signal - negative momentum or momentum weakening
            elif (current_row['momentum'] < -momentum_threshold/2 and position == 1):
                confidence = min(0.9, abs(current_row['momentum']) / momentum_threshold)
                
                signal = TradeSignal(
                    timestamp=current_row['timestamp'],
                    action='sell',
                    quantity=0,
                    price=current_row['close'],
                    confidence=confidence,
                    reasoning=f"Momentum sell: {current_row['momentum']:.2%} negative momentum"
                )
                signals.append(signal)
                position = 0
        
        return signals


class StrategyManager:
    """Manager for trading strategies"""
    
    def __init__(self):
        self.strategies = {
            'buy_and_hold': BuyAndHoldStrategy,
            'moving_average_crossover': MovingAverageCrossoverStrategy,
            'rsi': RSIStrategy,
            'mean_reversion': MeanReversionStrategy,
            'momentum': MomentumStrategy
        }
    
    def get_strategy(self, config: StrategyConfig) -> BaseStrategy:
        """Get strategy instance by name"""
        strategy_class = self.strategies.get(config.strategy_name.lower())
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {config.strategy_name}")
        return strategy_class(config)
    
    def list_strategies(self) -> List[str]:
        """List available strategies"""
        return list(self.strategies.keys())
    
    def add_strategy(self, name: str, strategy_class: type) -> None:
        """Add a custom strategy"""
        self.strategies[name] = strategy_class