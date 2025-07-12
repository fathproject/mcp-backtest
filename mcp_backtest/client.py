"""
Client library for MCP Backtest
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from .core.models import (
    BacktestRequest, BacktestResult, DataSourceConfig, 
    StrategyConfig, LLMConfig, BacktestConfig, MarketType,
    DataFormat, LLMProvider
)
from .core.backtest import BacktestEngine
from .data.handlers import DataHandler
from .strategies.base import StrategyManager
from .llm.providers import LLMManager


class BacktestClient:
    """Client for MCP Backtest services"""
    
    def __init__(self):
        self.data_handler = DataHandler()
        self.strategy_manager = StrategyManager()
        self.llm_manager = LLMManager()
    
    async def load_data_from_csv(self, file_path: str, market_type: str = "crypto", symbol: str = "UNKNOWN"):
        """Load data from CSV file"""
        config = DataSourceConfig(
            source_type=DataFormat.CSV,
            source_path=file_path
        )
        return await self.data_handler.load_data(config, MarketType(market_type), symbol)
    
    async def load_data_from_json(self, file_path: str, market_type: str = "crypto", symbol: str = "UNKNOWN"):
        """Load data from JSON file"""
        config = DataSourceConfig(
            source_type=DataFormat.JSON,
            source_path=file_path
        )
        return await self.data_handler.load_data(config, MarketType(market_type), symbol)
    
    async def load_data_from_api(self, endpoint: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None, 
                                market_type: str = "crypto", symbol: str = "UNKNOWN"):
        """Load data from API endpoint"""
        config = DataSourceConfig(
            source_type=DataFormat.API,
            api_endpoint=endpoint,
            api_headers=headers or {},
            api_params=params or {}
        )
        return await self.data_handler.load_data(config, MarketType(market_type), symbol)
    
    async def run_backtest(self, data, strategy: str, market_type: str, llm_model: str = "gpt-3.5-turbo", 
                          llm_provider: str = "openai", strategy_params: Dict[str, Any] = None,
                          initial_capital: float = 10000, commission: float = 0.001):
        """Run backtest with provided data"""
        
        # Create configurations
        strategy_config = StrategyConfig(
            strategy_name=strategy,
            parameters=strategy_params or {},
            risk_management={}
        )
        
        llm_config = LLMConfig(
            provider=LLMProvider(llm_provider),
            model_name=llm_model
        )
        
        backtest_config = BacktestConfig(
            initial_capital=initial_capital,
            commission=commission
        )
        
        # Create dummy request (data already loaded)
        request = BacktestRequest(
            data_source=DataSourceConfig(source_type=DataFormat.CSV, source_path=""),
            market_type=MarketType(market_type),
            strategy=strategy_config,
            backtest_config=backtest_config,
            llm_config=llm_config,
            analysis_requirements=[]
        )
        
        # Get strategy and generate signals
        strategy_instance = self.strategy_manager.get_strategy(strategy_config)
        signals = await strategy_instance.generate_signals(data)
        
        # Run backtest
        engine = BacktestEngine(backtest_config)
        result = await engine.run_backtest(request, data, signals)
        
        # Setup LLM and generate analysis
        self.llm_manager.add_provider(llm_config)
        analysis = await self.llm_manager.analyze_results(
            llm_config.provider, 
            result
        )
        
        # Update result with analysis
        result.analysis = analysis
        
        return result
    
    def list_strategies(self) -> List[str]:
        """List available strategies"""
        return self.strategy_manager.list_strategies()
    
    async def analyze_data(self, data, llm_provider: str = "openai", llm_model: str = "gpt-3.5-turbo", 
                          context: str = "General market analysis"):
        """Analyze market data using LLM"""
        llm_config = LLMConfig(
            provider=LLMProvider(llm_provider),
            model_name=llm_model
        )
        
        self.llm_manager.add_provider(llm_config)
        
        analysis = await self.llm_manager.generate_analysis(
            llm_config.provider, 
            data, 
            context
        )
        
        return analysis
    
    async def generate_strategy(self, data, requirements: str, llm_provider: str = "openai", 
                               llm_model: str = "gpt-3.5-turbo"):
        """Generate trading strategy using LLM"""
        llm_config = LLMConfig(
            provider=LLMProvider(llm_provider),
            model_name=llm_model
        )
        
        self.llm_manager.add_provider(llm_config)
        
        strategy = await self.llm_manager.generate_strategy(
            llm_config.provider, 
            data, 
            requirements
        )
        
        return strategy


class BacktestResultAnalyzer:
    """Analyzer for backtest results"""
    
    def __init__(self, result: BacktestResult):
        self.result = result
    
    def get_result_matrix(self) -> Dict[str, Any]:
        """Get result matrix"""
        return self.result.result_matrix
    
    def get_performance_summary(self) -> Dict[str, float]:
        """Get performance summary"""
        return self.result.result_matrix.get('performance_summary', {})
    
    def get_trade_analysis(self) -> Dict[str, Any]:
        """Get trade analysis"""
        return self.result.result_matrix.get('trade_analysis', {})
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get risk metrics"""
        return self.result.result_matrix.get('risk_metrics', {})
    
    def get_market_comparison(self) -> Dict[str, float]:
        """Get market comparison"""
        return self.result.result_matrix.get('market_comparison', {})
    
    def export_results(self, file_path: str) -> None:
        """Export results to file"""
        with open(file_path, 'w') as f:
            json.dump(self.result.dict(), f, indent=2, default=str)
    
    def print_summary(self) -> None:
        """Print summary of results"""
        perf = self.get_performance_summary()
        trade = self.get_trade_analysis()
        risk = self.get_risk_metrics()
        
        print(f"=== Backtest Results Summary ===")
        print(f"Strategy: {self.result.request.strategy.strategy_name}")
        print(f"Market: {self.result.request.market_type}")
        print(f"Test ID: {self.result.test_id}")
        print(f"")
        print(f"Performance Metrics:")
        print(f"  Total Return: {perf.get('total_return_pct', 0):.2f}%")
        print(f"  Annualized Return: {perf.get('annualized_return_pct', 0):.2f}%")
        print(f"  Volatility: {perf.get('volatility_pct', 0):.2f}%")
        print(f"  Sharpe Ratio: {perf.get('sharpe_ratio', 0):.2f}")
        print(f"  Max Drawdown: {perf.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Win Rate: {perf.get('win_rate_pct', 0):.2f}%")
        print(f"  Profit Factor: {perf.get('profit_factor', 0):.2f}")
        print(f"")
        print(f"Trade Analysis:")
        print(f"  Total Trades: {trade.get('total_trades', 0)}")
        print(f"  Winning Trades: {trade.get('winning_trades', 0)}")
        print(f"  Losing Trades: {trade.get('losing_trades', 0)}")
        print(f"  Average Win: ${trade.get('avg_win', 0):.2f}")
        print(f"  Average Loss: ${trade.get('avg_loss', 0):.2f}")
        print(f"  Largest Win: ${trade.get('largest_win', 0):.2f}")
        print(f"  Largest Loss: ${trade.get('largest_loss', 0):.2f}")
        print(f"")
        print(f"Risk Metrics:")
        print(f"  VaR 95%: {risk.get('value_at_risk_95', 0):.4f}")
        print(f"  CVaR 95%: {risk.get('conditional_var_95', 0):.4f}")
        print(f"  Max Consecutive Losses: {risk.get('max_consecutive_losses', 0)}")
        print(f"")
        print(f"AI Analysis:")
        print(f"{self.result.analysis}")


# Example usage functions
async def example_csv_backtest():
    """Example CSV backtest"""
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
        strategy_params={"short_window": 10, "long_window": 30},
        initial_capital=10000,
        commission=0.001
    )
    
    # Analyze results
    analyzer = BacktestResultAnalyzer(result)
    analyzer.print_summary()
    
    return result


async def example_json_backtest():
    """Example JSON backtest"""
    client = BacktestClient()
    
    # Load data from JSON
    data = await client.load_data_from_json("data/eth_usd.json", "crypto", "ETH/USD")
    
    # Run backtest
    result = await client.run_backtest(
        data=data,
        strategy="rsi",
        market_type="crypto",
        llm_model="gpt-4",
        llm_provider="openai",
        strategy_params={"rsi_period": 14, "oversold_level": 30, "overbought_level": 70},
        initial_capital=10000,
        commission=0.001
    )
    
    # Analyze results
    analyzer = BacktestResultAnalyzer(result)
    analyzer.print_summary()
    analyzer.export_results("results/eth_rsi_backtest.json")
    
    return result


async def example_api_backtest():
    """Example API backtest"""
    client = BacktestClient()
    
    # Load data from API
    data = await client.load_data_from_api(
        endpoint="https://api.example.com/ohlcv",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
        params={"symbol": "AAPL", "interval": "1d", "limit": 1000},
        market_type="stock",
        symbol="AAPL"
    )
    
    # Run backtest
    result = await client.run_backtest(
        data=data,
        strategy="mean_reversion",
        market_type="stock",
        llm_model="claude-3-sonnet-20240229",
        llm_provider="claude",
        strategy_params={"window": 20, "std_dev": 2},
        initial_capital=10000,
        commission=0.001
    )
    
    # Analyze results
    analyzer = BacktestResultAnalyzer(result)
    analyzer.print_summary()
    
    return result


async def example_market_analysis():
    """Example market analysis"""
    client = BacktestClient()
    
    # Load data
    data = await client.load_data_from_csv("data/btc_usd.csv", "crypto", "BTC/USD")
    
    # Analyze market
    analysis = await client.analyze_data(
        data=data,
        llm_provider="openai",
        llm_model="gpt-4",
        context="Analyze Bitcoin market trends and identify potential trading opportunities"
    )
    
    print("Market Analysis:")
    print(analysis)
    
    return analysis


async def example_strategy_generation():
    """Example strategy generation"""
    client = BacktestClient()
    
    # Load data
    data = await client.load_data_from_csv("data/btc_usd.csv", "crypto", "BTC/USD")
    
    # Generate strategy
    strategy = await client.generate_strategy(
        data=data,
        requirements="Create a momentum-based strategy for Bitcoin trading with risk management",
        llm_provider="openai",
        llm_model="gpt-4"
    )
    
    print("Generated Strategy:")
    print(strategy)
    
    return strategy


if __name__ == "__main__":
    # Run example
    asyncio.run(example_csv_backtest())