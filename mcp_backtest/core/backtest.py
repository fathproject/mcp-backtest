"""
Backtesting engine for financial strategies
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ..core.models import (
    MarketData, BacktestConfig, BacktestResult, TradeSignal, 
    PerformanceMetrics, BacktestRequest
)


class BacktestEngine:
    """Core backtesting engine"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.initial_capital = config.initial_capital
        self.commission = config.commission
        self.slippage = config.slippage
        
        # Portfolio state
        self.current_capital = config.initial_capital
        self.position = 0.0
        self.position_value = 0.0
        self.trades = []
        self.portfolio_history = []
        
    async def run_backtest(self, request: BacktestRequest, market_data: MarketData, strategy_signals: List[TradeSignal]) -> BacktestResult:
        """Run complete backtest"""
        
        # Initialize portfolio
        self._initialize_portfolio()
        
        # Process signals chronologically
        sorted_signals = sorted(strategy_signals, key=lambda x: x.timestamp)
        
        # Create price lookup for efficiency
        price_lookup = {price.timestamp: price for price in market_data.data}
        
        # Process each signal
        for signal in sorted_signals:
            if signal.timestamp in price_lookup:
                current_price = price_lookup[signal.timestamp]
                await self._process_signal(signal, current_price)
        
        # Calculate final portfolio value
        final_price = market_data.data[-1] if market_data.data else None
        if final_price and self.position != 0:
            # Close any remaining position
            await self._close_position(final_price)
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        # Generate result matrix
        result_matrix = self._generate_result_matrix(metrics, market_data)
        
        # Create result
        result = BacktestResult(
            test_id=str(uuid.uuid4()),
            request=request,
            trades=self.trades,
            metrics=metrics,
            analysis="",  # Will be filled by LLM
            result_matrix=result_matrix,
            created_at=datetime.now()
        )
        
        return result
    
    def _initialize_portfolio(self) -> None:
        """Initialize portfolio state"""
        self.current_capital = self.initial_capital
        self.position = 0.0
        self.position_value = 0.0
        self.trades = []
        self.portfolio_history = []
    
    async def _process_signal(self, signal: TradeSignal, current_price) -> None:
        """Process a trading signal"""
        if signal.action.lower() == 'buy':
            await self._execute_buy(signal, current_price)
        elif signal.action.lower() == 'sell':
            await self._execute_sell(signal, current_price)
        # 'hold' signals don't require action
        
        # Record portfolio state
        self._record_portfolio_state(signal.timestamp, current_price)
    
    async def _execute_buy(self, signal: TradeSignal, current_price) -> None:
        """Execute a buy order"""
        if self.current_capital <= 0:
            return  # No capital to buy
        
        # Calculate actual execution price with slippage
        execution_price = current_price.close * (1 + self.slippage)
        
        # Calculate quantity based on signal or available capital
        if signal.quantity > 0:
            quantity = min(signal.quantity, self.current_capital / execution_price)
        else:
            # Use all available capital
            quantity = self.current_capital / execution_price
        
        # Calculate costs
        trade_value = quantity * execution_price
        commission_cost = trade_value * self.commission
        total_cost = trade_value + commission_cost
        
        if total_cost <= self.current_capital:
            # Execute trade
            self.current_capital -= total_cost
            self.position += quantity
            self.position_value += trade_value
            
            # Record trade
            trade = TradeSignal(
                timestamp=signal.timestamp,
                action='buy',
                quantity=quantity,
                price=execution_price,
                confidence=signal.confidence,
                reasoning=signal.reasoning
            )
            self.trades.append(trade)
    
    async def _execute_sell(self, signal: TradeSignal, current_price) -> None:
        """Execute a sell order"""
        if self.position <= 0:
            return  # No position to sell
        
        # Calculate actual execution price with slippage
        execution_price = current_price.close * (1 - self.slippage)
        
        # Calculate quantity to sell
        if signal.quantity > 0:
            quantity = min(signal.quantity, self.position)
        else:
            # Sell entire position
            quantity = self.position
        
        # Calculate proceeds
        trade_value = quantity * execution_price
        commission_cost = trade_value * self.commission
        net_proceeds = trade_value - commission_cost
        
        # Execute trade
        self.current_capital += net_proceeds
        self.position -= quantity
        self.position_value -= quantity * execution_price
        
        # Record trade
        trade = TradeSignal(
            timestamp=signal.timestamp,
            action='sell',
            quantity=quantity,
            price=execution_price,
            confidence=signal.confidence,
            reasoning=signal.reasoning
        )
        self.trades.append(trade)
    
    async def _close_position(self, final_price) -> None:
        """Close any remaining position at the end"""
        if self.position > 0:
            execution_price = final_price.close * (1 - self.slippage)
            trade_value = self.position * execution_price
            commission_cost = trade_value * self.commission
            net_proceeds = trade_value - commission_cost
            
            self.current_capital += net_proceeds
            
            # Record final trade
            trade = TradeSignal(
                timestamp=final_price.timestamp,
                action='sell',
                quantity=self.position,
                price=execution_price,
                confidence=1.0,
                reasoning='Final position close'
            )
            self.trades.append(trade)
            
            self.position = 0.0
            self.position_value = 0.0
    
    def _record_portfolio_state(self, timestamp: datetime, current_price) -> None:
        """Record current portfolio state"""
        current_position_value = self.position * current_price.close
        total_value = self.current_capital + current_position_value
        
        state = {
            'timestamp': timestamp,
            'capital': self.current_capital,
            'position': self.position,
            'position_value': current_position_value,
            'total_value': total_value,
            'price': current_price.close
        }
        
        self.portfolio_history.append(state)
    
    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not self.portfolio_history:
            return {}
        
        # Convert to DataFrame for easier calculation
        df = pd.DataFrame(self.portfolio_history)
        
        # Calculate returns
        df['returns'] = df['total_value'].pct_change().fillna(0)
        df['cumulative_returns'] = (1 + df['returns']).cumprod()
        
        # Basic metrics
        final_value = df['total_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Annualized return (assuming daily data)
        trading_days = len(df)
        if trading_days > 0:
            annualized_return = ((1 + total_return) ** (252 / trading_days)) - 1
        else:
            annualized_return = 0
        
        # Volatility
        volatility = df['returns'].std() * np.sqrt(252)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        if volatility > 0:
            sharpe_ratio = annualized_return / volatility
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        running_max = df['total_value'].expanding().max()
        drawdown = (df['total_value'] - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t.action == 'sell']
        buy_trades = [t for t in self.trades if t.action == 'buy']
        
        # Calculate trade P&L
        trade_pnl = []
        if len(buy_trades) > 0 and len(winning_trades) > 0:
            # Simple P&L calculation (this could be more sophisticated)
            for i, sell_trade in enumerate(winning_trades):
                if i < len(buy_trades):
                    buy_trade = buy_trades[i]
                    pnl = (sell_trade.price - buy_trade.price) * min(sell_trade.quantity, buy_trade.quantity)
                    trade_pnl.append(pnl)
        
        # Trade statistics
        total_trades = len(self.trades)
        winning_trade_count = len([pnl for pnl in trade_pnl if pnl > 0])
        losing_trade_count = len([pnl for pnl in trade_pnl if pnl < 0])
        
        win_rate = winning_trade_count / len(trade_pnl) if trade_pnl else 0
        
        avg_win = np.mean([pnl for pnl in trade_pnl if pnl > 0]) if winning_trade_count > 0 else 0
        avg_loss = np.mean([pnl for pnl in trade_pnl if pnl < 0]) if losing_trade_count > 0 else 0
        
        profit_factor = abs(avg_win * winning_trade_count / (avg_loss * losing_trade_count)) if avg_loss != 0 and losing_trade_count > 0 else 0
        
        largest_win = max(trade_pnl) if trade_pnl else 0
        largest_loss = min(trade_pnl) if trade_pnl else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'winning_trades': winning_trade_count,
            'losing_trades': losing_trade_count,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'final_value': final_value,
            'initial_capital': self.initial_capital
        }
    
    def _generate_result_matrix(self, metrics: Dict[str, float], market_data: MarketData) -> Dict[str, any]:
        """Generate comprehensive result matrix"""
        
        # Performance summary
        performance_summary = {
            'total_return_pct': metrics.get('total_return', 0) * 100,
            'annualized_return_pct': metrics.get('annualized_return', 0) * 100,
            'volatility_pct': metrics.get('volatility', 0) * 100,
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'max_drawdown_pct': metrics.get('max_drawdown', 0) * 100,
            'profit_factor': metrics.get('profit_factor', 0),
            'win_rate_pct': metrics.get('win_rate', 0) * 100
        }
        
        # Trade analysis
        trade_analysis = {
            'total_trades': metrics.get('total_trades', 0),
            'winning_trades': metrics.get('winning_trades', 0),
            'losing_trades': metrics.get('losing_trades', 0),
            'avg_win': metrics.get('avg_win', 0),
            'avg_loss': metrics.get('avg_loss', 0),
            'largest_win': metrics.get('largest_win', 0),
            'largest_loss': metrics.get('largest_loss', 0)
        }
        
        # Risk metrics
        risk_metrics = {
            'value_at_risk_95': self._calculate_var(0.95) if self.portfolio_history else 0,
            'value_at_risk_99': self._calculate_var(0.99) if self.portfolio_history else 0,
            'conditional_var_95': self._calculate_cvar(0.95) if self.portfolio_history else 0,
            'max_consecutive_losses': self._calculate_max_consecutive_losses()
        }
        
        # Portfolio evolution
        portfolio_evolution = []
        for state in self.portfolio_history[-100:]:  # Last 100 points
            portfolio_evolution.append({
                'timestamp': state['timestamp'].isoformat(),
                'total_value': state['total_value'],
                'capital': state['capital'],
                'position_value': state['position_value']
            })
        
        # Market comparison
        market_comparison = self._calculate_market_comparison(market_data)
        
        result_matrix = {
            'performance_summary': performance_summary,
            'trade_analysis': trade_analysis,
            'risk_metrics': risk_metrics,
            'portfolio_evolution': portfolio_evolution,
            'market_comparison': market_comparison,
            'backtest_config': {
                'initial_capital': self.initial_capital,
                'commission': self.commission,
                'slippage': self.slippage
            }
        }
        
        return result_matrix
    
    def _calculate_var(self, confidence_level: float) -> float:
        """Calculate Value at Risk"""
        if not self.portfolio_history:
            return 0
        
        df = pd.DataFrame(self.portfolio_history)
        returns = df['total_value'].pct_change().dropna()
        
        if len(returns) == 0:
            return 0
        
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    def _calculate_cvar(self, confidence_level: float) -> float:
        """Calculate Conditional Value at Risk"""
        if not self.portfolio_history:
            return 0
        
        df = pd.DataFrame(self.portfolio_history)
        returns = df['total_value'].pct_change().dropna()
        
        if len(returns) == 0:
            return 0
        
        var = self._calculate_var(confidence_level)
        return returns[returns <= var].mean()
    
    def _calculate_max_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losses"""
        if not self.trades:
            return 0
        
        # Calculate trade P&L (simplified)
        consecutive_losses = 0
        max_consecutive = 0
        
        buy_trades = [t for t in self.trades if t.action == 'buy']
        sell_trades = [t for t in self.trades if t.action == 'sell']
        
        for i, sell_trade in enumerate(sell_trades):
            if i < len(buy_trades):
                buy_trade = buy_trades[i]
                pnl = (sell_trade.price - buy_trade.price) * min(sell_trade.quantity, buy_trade.quantity)
                
                if pnl < 0:
                    consecutive_losses += 1
                    max_consecutive = max(max_consecutive, consecutive_losses)
                else:
                    consecutive_losses = 0
        
        return max_consecutive
    
    def _calculate_market_comparison(self, market_data: MarketData) -> Dict[str, float]:
        """Calculate comparison with market performance"""
        if not market_data.data or len(market_data.data) < 2:
            return {}
        
        initial_price = market_data.data[0].close
        final_price = market_data.data[-1].close
        
        market_return = (final_price - initial_price) / initial_price
        strategy_return = self.portfolio_history[-1]['total_value'] / self.initial_capital - 1 if self.portfolio_history else 0
        
        return {
            'market_return_pct': market_return * 100,
            'strategy_return_pct': strategy_return * 100,
            'excess_return_pct': (strategy_return - market_return) * 100,
            'market_initial_price': initial_price,
            'market_final_price': final_price
        }