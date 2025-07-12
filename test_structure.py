#!/usr/bin/env python3
"""
Test script to validate the basic structure of MCP Backtest
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that we can import our modules"""
    print("Testing imports...")
    
    try:
        # Test basic imports
        from mcp_backtest import __version__
        print(f"✓ MCP Backtest version: {__version__}")
        
        from mcp_backtest.core.models import (
            MarketType, DataFormat, LLMProvider, PriceData, 
            BacktestRequest, BacktestResult
        )
        print("✓ Core models imported successfully")
        
        from mcp_backtest.core.backtest import BacktestEngine
        print("✓ Backtest engine imported successfully")
        
        from mcp_backtest.strategies.base import (
            BuyAndHoldStrategy, MovingAverageCrossoverStrategy,
            RSIStrategy, MeanReversionStrategy, MomentumStrategy,
            StrategyManager
        )
        print("✓ Strategies imported successfully")
        
        from mcp_backtest.data.handlers import DataHandler
        print("✓ Data handlers imported successfully")
        
        from mcp_backtest.llm.providers import LLMManager
        print("✓ LLM providers imported successfully")
        
        from mcp_backtest.config import Config
        print("✓ Configuration imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_models():
    """Test that we can create model instances"""
    print("\nTesting model creation...")
    
    try:
        from mcp_backtest.core.models import (
            MarketType, DataFormat, LLMProvider, PriceData, 
            BacktestConfig, StrategyConfig, LLMConfig
        )
        from datetime import datetime
        
        # Test PriceData
        price_data = PriceData(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0
        )
        print(f"✓ PriceData created: {price_data.close}")
        
        # Test BacktestConfig
        backtest_config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001
        )
        print(f"✓ BacktestConfig created: {backtest_config.initial_capital}")
        
        # Test StrategyConfig
        strategy_config = StrategyConfig(
            strategy_name="moving_average_crossover",
            parameters={"short_window": 10, "long_window": 30}
        )
        print(f"✓ StrategyConfig created: {strategy_config.strategy_name}")
        
        # Test LLMConfig
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-3.5-turbo"
        )
        print(f"✓ LLMConfig created: {llm_config.provider}")
        
        return True
        
    except Exception as e:
        print(f"✗ Model creation error: {e}")
        return False


def test_strategies():
    """Test that we can create strategy instances"""
    print("\nTesting strategy creation...")
    
    try:
        from mcp_backtest.strategies.base import StrategyManager
        from mcp_backtest.core.models import StrategyConfig
        
        strategy_manager = StrategyManager()
        strategies = strategy_manager.list_strategies()
        
        print(f"✓ Available strategies: {strategies}")
        
        # Test creating a strategy
        config = StrategyConfig(
            strategy_name="buy_and_hold",
            parameters={}
        )
        
        strategy = strategy_manager.get_strategy(config)
        print(f"✓ Strategy created: {strategy.name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Strategy creation error: {e}")
        return False


def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from mcp_backtest.config import Config
        
        config = Config()
        print(f"✓ Config created: {config.app_name} v{config.version}")
        print(f"✓ Environment: {config.environment}")
        print(f"✓ Data directory: {config.data_dir}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_data_generator():
    """Test the data generator"""
    print("\nTesting data generation...")
    
    try:
        from examples.data_generator import generate_sample_crypto_data
        
        # Generate sample data
        data = generate_sample_crypto_data("BTC/USD", days=30)
        
        print(f"✓ Generated {len(data)} data points")
        print(f"✓ Columns: {list(data.columns)}")
        print(f"✓ Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Data generation error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=== MCP Backtest Structure Validation ===\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Model Test", test_models),
        ("Strategy Test", test_strategies),
        ("Configuration Test", test_configuration),
        ("Data Generator Test", test_data_generator)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✓ {test_name} PASSED")
                passed += 1
            else:
                print(f"✗ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} FAILED: {e}")
            failed += 1
        
        print("-" * 50)
    
    print(f"\n=== Test Summary ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The MCP Backtest structure is working correctly.")
        return True
    else:
        print(f"\n❌ {failed} tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)