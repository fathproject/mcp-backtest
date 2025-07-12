"""
Example usage scripts for MCP Backtest
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import mcp_backtest
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_backtest.client import BacktestClient, BacktestResultAnalyzer
from examples.data_generator import create_sample_data_files


async def example_basic_backtest():
    """Basic backtest example"""
    print("=== Running Basic Backtest Example ===")
    
    # Create sample data if it doesn't exist
    create_sample_data_files()
    
    # Initialize client
    client = BacktestClient()
    
    # Load data from CSV
    print("Loading BTC/USD data...")
    data = await client.load_data_from_csv(
        "examples/data/btc_usd_sample.csv", 
        "crypto", 
        "BTC/USD"
    )
    
    print(f"Loaded {len(data.data)} data points")
    
    # Run backtest with moving average crossover strategy
    print("Running backtest with moving average crossover strategy...")
    
    # Note: This will use a mock LLM provider since we don't have real API keys
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
    print("\n=== Results ===")
    analyzer = BacktestResultAnalyzer(result)
    analyzer.print_summary()
    
    # Export results
    Path("examples/results").mkdir(exist_ok=True)
    analyzer.export_results("examples/results/btc_ma_backtest.json")
    print(f"\nResults exported to examples/results/btc_ma_backtest.json")
    
    return result


async def example_multi_strategy_comparison():
    """Compare multiple strategies"""
    print("\n=== Running Multi-Strategy Comparison ===")
    
    # Create sample data if it doesn't exist
    create_sample_data_files()
    
    # Initialize client
    client = BacktestClient()
    
    # Load data
    print("Loading AAPL data...")
    data = await client.load_data_from_csv(
        "examples/data/aapl_sample.csv", 
        "stock", 
        "AAPL"
    )
    
    strategies = [
        ("buy_and_hold", {}),
        ("moving_average_crossover", {"short_window": 10, "long_window": 30}),
        ("rsi", {"rsi_period": 14, "oversold_level": 30, "overbought_level": 70}),
        ("mean_reversion", {"window": 20, "std_dev": 2}),
        ("momentum", {"lookback_period": 10, "momentum_threshold": 0.02})
    ]
    
    results = []
    
    for strategy_name, params in strategies:
        print(f"\nRunning {strategy_name} strategy...")
        
        try:
            result = await client.run_backtest(
                data=data,
                strategy=strategy_name,
                market_type="stock",
                llm_model="gpt-3.5-turbo",
                llm_provider="openai",
                strategy_params=params,
                initial_capital=10000,
                commission=0.001
            )
            
            results.append((strategy_name, result))
            
            # Print quick summary
            perf = result.result_matrix.get('performance_summary', {})
            print(f"  Total Return: {perf.get('total_return_pct', 0):.2f}%")
            print(f"  Sharpe Ratio: {perf.get('sharpe_ratio', 0):.2f}")
            print(f"  Max Drawdown: {perf.get('max_drawdown_pct', 0):.2f}%")
            
        except Exception as e:
            print(f"  Error running {strategy_name}: {e}")
    
    # Print comparison
    print("\n=== Strategy Comparison ===")
    print(f"{'Strategy':<25} {'Return':<10} {'Sharpe':<8} {'Drawdown':<12} {'Trades':<8}")
    print("-" * 70)
    
    for strategy_name, result in results:
        perf = result.result_matrix.get('performance_summary', {})
        trade = result.result_matrix.get('trade_analysis', {})
        
        print(f"{strategy_name:<25} "
              f"{perf.get('total_return_pct', 0):>9.2f}% "
              f"{perf.get('sharpe_ratio', 0):>7.2f} "
              f"{perf.get('max_drawdown_pct', 0):>11.2f}% "
              f"{trade.get('total_trades', 0):>7}")
    
    return results


async def example_market_analysis():
    """Market analysis example"""
    print("\n=== Running Market Analysis Example ===")
    
    # Create sample data if it doesn't exist
    create_sample_data_files()
    
    # Initialize client
    client = BacktestClient()
    
    # Load data
    print("Loading EUR/USD data...")
    data = await client.load_data_from_csv(
        "examples/data/eurusd_sample.csv", 
        "forex", 
        "EUR/USD"
    )
    
    # Analyze market
    print("Analyzing market data...")
    
    try:
        analysis = await client.analyze_data(
            data=data,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            context="Analyze EUR/USD forex market trends and identify potential trading opportunities"
        )
        
        print("\n=== Market Analysis ===")
        print(analysis)
        
    except Exception as e:
        print(f"Error in market analysis: {e}")
        print("Note: This likely failed due to missing API keys. Set OPENAI_API_KEY in your environment.")
    
    return data


async def example_strategy_generation():
    """Strategy generation example"""
    print("\n=== Running Strategy Generation Example ===")
    
    # Create sample data if it doesn't exist
    create_sample_data_files()
    
    # Initialize client
    client = BacktestClient()
    
    # Load data
    print("Loading BTC/USD data...")
    data = await client.load_data_from_csv(
        "examples/data/btc_usd_sample.csv", 
        "crypto", 
        "BTC/USD"
    )
    
    # Generate strategy
    print("Generating trading strategy...")
    
    try:
        strategy = await client.generate_strategy(
            data=data,
            requirements="Create a momentum-based strategy for Bitcoin trading with proper risk management. "
                        "The strategy should include stop-loss and take-profit levels, position sizing rules, "
                        "and market condition filters.",
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        print("\n=== Generated Strategy ===")
        print(strategy)
        
    except Exception as e:
        print(f"Error in strategy generation: {e}")
        print("Note: This likely failed due to missing API keys. Set OPENAI_API_KEY in your environment.")
    
    return data


async def example_json_api_backtest():
    """JSON and API backtest example"""
    print("\n=== Running JSON/API Backtest Example ===")
    
    # Create sample data if it doesn't exist
    create_sample_data_files()
    
    # Initialize client
    client = BacktestClient()
    
    # Load data from JSON
    print("Loading BTC/USD data from JSON...")
    data = await client.load_data_from_json(
        "examples/data/btc_usd_sample.json", 
        "crypto", 
        "BTC/USD"
    )
    
    print(f"Loaded {len(data.data)} data points from JSON")
    
    # Run backtest with RSI strategy
    print("Running backtest with RSI strategy...")
    
    result = await client.run_backtest(
        data=data,
        strategy="rsi",
        market_type="crypto",
        llm_model="gpt-3.5-turbo",
        llm_provider="openai",
        strategy_params={"rsi_period": 14, "oversold_level": 30, "overbought_level": 70},
        initial_capital=10000,
        commission=0.001
    )
    
    # Analyze results
    print("\n=== Results ===")
    analyzer = BacktestResultAnalyzer(result)
    analyzer.print_summary()
    
    return result


async def run_all_examples():
    """Run all examples"""
    print("=== Running All MCP Backtest Examples ===")
    
    examples = [
        example_basic_backtest,
        example_multi_strategy_comparison,
        example_market_analysis,
        example_strategy_generation,
        example_json_api_backtest
    ]
    
    for example in examples:
        try:
            await example()
            print("\n" + "="*60 + "\n")
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Run specific example or all examples
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        
        examples = {
            "basic": example_basic_backtest,
            "multi": example_multi_strategy_comparison,
            "analysis": example_market_analysis,
            "strategy": example_strategy_generation,
            "json": example_json_api_backtest,
            "all": run_all_examples
        }
        
        if example_name in examples:
            asyncio.run(examples[example_name]())
        else:
            print(f"Unknown example: {example_name}")
            print(f"Available examples: {list(examples.keys())}")
    else:
        # Run basic example by default
        asyncio.run(example_basic_backtest())