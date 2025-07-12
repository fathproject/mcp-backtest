"""
Live Trading Engine for executing strategies in real-time
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd

from .metaapi_client import MetaAPIClient, OrderType, Position
from ..strategies.base import BaseStrategy
from ..core.models import MarketType
from ..config import get_config

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading modes"""
    LIVE = "live"
    DEMO = "demo"
    PAPER = "paper"


class TradeSignal(Enum):
    """Trading signals"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class TradingState(Enum):
    """Trading engine states"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class LiveTradingEngine:
    """Live trading engine for executing strategies"""
    
    def __init__(self, strategy: BaseStrategy, symbols: List[str], 
                 mode: TradingMode = TradingMode.DEMO):
        self.strategy = strategy
        self.symbols = symbols
        self.mode = mode
        self.config = get_config()
        
        # Trading state
        self.state = TradingState.STOPPED
        self.client: Optional[MetaAPIClient] = None
        self.positions: Dict[str, Position] = {}
        self.orders: List[Dict[str, Any]] = []
        
        # Risk management
        self.risk_per_trade = self.config.metaapi.risk_limit
        self.max_positions = self.config.metaapi.max_positions
        self.max_daily_loss = self.config.metaapi.max_daily_loss
        
        # Trading data
        self.price_history: Dict[str, pd.DataFrame] = {}
        self.last_signals: Dict[str, TradeSignal] = {}
        
        # Callbacks
        self.on_trade_callback: Optional[Callable] = None
        self.on_signal_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        
        # Performance tracking
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.start_equity = 0.0
    
    async def start(self):
        """Start the trading engine"""
        try:
            self.client = MetaAPIClient()
            await self.client.__aenter__()
            
            # Validate account and symbols
            await self._validate_setup()
            
            # Initialize tracking
            self.start_equity = await self.client.get_account_equity()
            
            self.state = TradingState.RUNNING
            logger.info("Live trading engine started")
            
            # Start main trading loop
            await self._trading_loop()
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
            self.state = TradingState.ERROR
            if self.on_error_callback:
                await self.on_error_callback(e)
    
    async def stop(self):
        """Stop the trading engine"""
        self.state = TradingState.STOPPED
        if self.client:
            await self.client.__aexit__(None, None, None)
        logger.info("Live trading engine stopped")
    
    async def pause(self):
        """Pause the trading engine"""
        self.state = TradingState.PAUSED
        logger.info("Live trading engine paused")
    
    async def resume(self):
        """Resume the trading engine"""
        if self.state == TradingState.PAUSED:
            self.state = TradingState.RUNNING
            logger.info("Live trading engine resumed")
    
    async def _validate_setup(self):
        """Validate trading setup"""
        if not self.client:
            raise RuntimeError("MetaAPI client not initialized")
        
        # Check account connection
        account_info = await self.client.get_account_info()
        if not account_info:
            raise RuntimeError("Cannot connect to trading account")
        
        # Validate symbols
        for symbol in self.symbols:
            if not await self.client.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
        
        logger.info(f"Trading setup validated for {len(self.symbols)} symbols")
    
    async def _trading_loop(self):
        """Main trading loop"""
        while self.state == TradingState.RUNNING:
            try:
                # Check risk limits
                if await self._check_risk_limits():
                    logger.warning("Risk limits exceeded, pausing trading")
                    await self.pause()
                    continue
                
                # Update positions and orders
                await self._update_positions()
                await self._update_orders()
                
                # Process each symbol
                for symbol in self.symbols:
                    if self.state != TradingState.RUNNING:
                        break
                    
                    await self._process_symbol(symbol)
                
                # Wait before next iteration
                await asyncio.sleep(60)  # 1 minute intervals
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                self.state = TradingState.ERROR
                if self.on_error_callback:
                    await self.on_error_callback(e)
    
    async def _check_risk_limits(self) -> bool:
        """Check if risk limits are exceeded"""
        try:
            current_equity = await self.client.get_account_equity()
            
            # Check daily loss limit
            self.daily_pnl = current_equity - self.start_equity
            daily_loss_pct = abs(self.daily_pnl / self.start_equity) if self.start_equity > 0 else 0
            
            if daily_loss_pct > self.max_daily_loss:
                logger.warning(f"Daily loss limit exceeded: {daily_loss_pct:.2%}")
                return True
            
            # Check maximum positions
            if len(self.positions) >= self.max_positions:
                logger.warning(f"Maximum positions reached: {len(self.positions)}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return True
    
    async def _update_positions(self):
        """Update current positions"""
        try:
            positions = await self.client.get_positions()
            self.positions = {pos.symbol: pos for pos in positions}
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    async def _update_orders(self):
        """Update pending orders"""
        try:
            self.orders = await self.client.get_orders()
        except Exception as e:
            logger.error(f"Error updating orders: {e}")
    
    async def _process_symbol(self, symbol: str):
        """Process trading signals for a symbol"""
        try:
            # Get latest price data
            price_data = await self._get_price_data(symbol)
            if price_data is None or price_data.empty:
                return
            
            # Generate trading signal
            signal = await self._generate_signal(symbol, price_data)
            
            # Execute trading logic
            await self._execute_signal(symbol, signal)
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
    
    async def _get_price_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get price data for symbol"""
        try:
            # Get historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)  # 24 hours of data
            
            candles = await self.client.get_history(symbol, "1h", start_time, end_time)
            
            if not candles:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            
            # Standardize columns
            if 'time' in df.columns:
                df['timestamp'] = pd.to_datetime(df['time'])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Store in history
            self.price_history[symbol] = df
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return None
    
    async def _generate_signal(self, symbol: str, price_data: pd.DataFrame) -> TradeSignal:
        """Generate trading signal using strategy"""
        try:
            # Apply strategy
            signals = self.strategy.generate_signals(price_data)
            
            if signals is None or signals.empty:
                return TradeSignal.HOLD
            
            # Get latest signal
            latest_signal = signals.iloc[-1]
            
            # Convert to TradeSignal
            if latest_signal.get('signal') == 1:
                signal = TradeSignal.BUY
            elif latest_signal.get('signal') == -1:
                signal = TradeSignal.SELL
            else:
                signal = TradeSignal.HOLD
            
            # Store signal
            self.last_signals[symbol] = signal
            
            # Callback
            if self.on_signal_callback:
                await self.on_signal_callback(symbol, signal, latest_signal)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return TradeSignal.HOLD
    
    async def _execute_signal(self, symbol: str, signal: TradeSignal):
        """Execute trading signal"""
        try:
            current_position = self.positions.get(symbol)
            
            if signal == TradeSignal.BUY:
                # Buy signal
                if not current_position:
                    await self._open_position(symbol, OrderType.BUY)
                elif current_position.type == "POSITION_TYPE_SELL":
                    # Close sell position and open buy
                    await self._close_position(symbol)
                    await self._open_position(symbol, OrderType.BUY)
            
            elif signal == TradeSignal.SELL:
                # Sell signal
                if not current_position:
                    await self._open_position(symbol, OrderType.SELL)
                elif current_position.type == "POSITION_TYPE_BUY":
                    # Close buy position and open sell
                    await self._close_position(symbol)
                    await self._open_position(symbol, OrderType.SELL)
            
            elif signal == TradeSignal.CLOSE:
                # Close any position
                if current_position:
                    await self._close_position(symbol)
            
            # HOLD signal does nothing
            
        except Exception as e:
            logger.error(f"Error executing signal for {symbol}: {e}")
    
    async def _open_position(self, symbol: str, order_type: OrderType):
        """Open a new position"""
        try:
            # Calculate position size
            position_size = await self.client.calculate_position_size(
                symbol, self.risk_per_trade * 100, 50  # 50 pips stop loss
            )
            
            # Get current price
            price_info = await self.client.get_price(symbol)
            current_price = price_info.get('bid' if order_type == OrderType.SELL else 'ask', 0)
            
            # Calculate stop loss and take profit
            stop_loss = self._calculate_stop_loss(current_price, order_type)
            take_profit = self._calculate_take_profit(current_price, order_type)
            
            # Place order
            result = await self.client.place_order(
                symbol=symbol,
                order_type=order_type,
                volume=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=f"Strategy: {self.strategy.name}"
            )
            
            logger.info(f"Opened {order_type.value} position for {symbol}: {result}")
            
            # Callback
            if self.on_trade_callback:
                await self.on_trade_callback("open", symbol, order_type, position_size, result)
            
            self.trades_today += 1
            
        except Exception as e:
            logger.error(f"Error opening position for {symbol}: {e}")
    
    async def _close_position(self, symbol: str):
        """Close existing position"""
        try:
            position = self.positions.get(symbol)
            if not position:
                return
            
            result = await self.client.close_position(position.id)
            
            logger.info(f"Closed position for {symbol}: {result}")
            
            # Callback
            if self.on_trade_callback:
                await self.on_trade_callback("close", symbol, None, position.volume, result)
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
    
    def _calculate_stop_loss(self, price: float, order_type: OrderType) -> float:
        """Calculate stop loss price"""
        # Simple 50 pips stop loss
        pip_value = 0.0001 if 'JPY' not in str(price) else 0.01
        stop_distance = 50 * pip_value
        
        if order_type == OrderType.BUY:
            return price - stop_distance
        else:
            return price + stop_distance
    
    def _calculate_take_profit(self, price: float, order_type: OrderType) -> float:
        """Calculate take profit price"""
        # Simple 100 pips take profit (2:1 risk-reward)
        pip_value = 0.0001 if 'JPY' not in str(price) else 0.01
        profit_distance = 100 * pip_value
        
        if order_type == OrderType.BUY:
            return price + profit_distance
        else:
            return price - profit_distance
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            "state": self.state.value,
            "symbols": self.symbols,
            "positions": len(self.positions),
            "orders": len(self.orders),
            "trades_today": self.trades_today,
            "daily_pnl": self.daily_pnl,
            "last_signals": {k: v.value for k, v in self.last_signals.items()}
        }
    
    def set_callbacks(self, on_trade: Optional[Callable] = None,
                     on_signal: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """Set callback functions"""
        self.on_trade_callback = on_trade
        self.on_signal_callback = on_signal
        self.on_error_callback = on_error