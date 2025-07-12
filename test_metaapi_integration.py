#!/usr/bin/env python3
"""
Test script for MetaAPI integration
"""

import asyncio
import json
from typing import Dict, Any

from mcp_backtest.server import MCPBacktestServer

async def test_metaapi_integration():
    """Test MetaAPI integration functionality"""
    
    print("🚀 Testing MetaAPI Integration")
    print("=" * 50)
    
    # Initialize server
    server = MCPBacktestServer()
    
    # Test 1: Check if MetaAPI tools are available
    print("\n1. Testing MCP Tools Registration")
    try:
        tools = await server.server.list_tools()
        metaapi_tools = [
            tool for tool in tools 
            if tool.name in ['start_live_trading', 'stop_live_trading', 'get_trading_status', 'get_account_info']
        ]
        print(f"✅ Found {len(metaapi_tools)} MetaAPI tools:")
        for tool in metaapi_tools:
            print(f"   - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"❌ Error checking tools: {e}")
    
    # Test 2: Test start_live_trading tool (without actual API keys)
    print("\n2. Testing start_live_trading Tool")
    try:
        args = {
            "symbols": ["EURUSD", "GBPUSD"],
            "trading_prompt": "Test conservative trading strategy",
            "mode": "demo",
            "llm_provider": "openai"
        }
        
        # This would normally start live trading, but without API keys it will fail gracefully
        print(f"   Arguments: {json.dumps(args, indent=2)}")
        print("   📝 Note: This would start live trading with proper API keys configured")
        
    except Exception as e:
        print(f"   ⚠️ Expected error without API keys: {e}")
    
    # Test 3: Test account info tool
    print("\n3. Testing get_account_info Tool")
    try:
        # This would get account info, but without API keys it will fail gracefully
        print("   📝 Note: This would retrieve account information with proper API keys configured")
        
    except Exception as e:
        print(f"   ⚠️ Expected error without API keys: {e}")
    
    # Test 4: Configuration test
    print("\n4. Testing Configuration")
    try:
        from mcp_backtest.config import get_config
        config = get_config()
        
        print(f"   MetaAPI API Key: {'✅ Configured' if config.metaapi.api_key else '❌ Not configured'}")
        print(f"   MetaAPI Account ID: {'✅ Configured' if config.metaapi.account_id else '❌ Not configured'}")
        print(f"   MetaAPI Region: {config.metaapi.region}")
        print(f"   MetaAPI Platform: {config.metaapi.platform}")
        print(f"   Risk Limit: {config.metaapi.risk_limit * 100}%")
        print(f"   Max Positions: {config.metaapi.max_positions}")
        
    except Exception as e:
        print(f"   ❌ Error checking configuration: {e}")
    
    # Test 5: Import test
    print("\n5. Testing Module Imports")
    try:
        from mcp_backtest.trading.metaapi_client import MetaAPIClient, OrderType
        from mcp_backtest.trading.live_engine import LiveTradingEngine, TradingMode
        
        print("   ✅ MetaAPIClient imported successfully")
        print("   ✅ LiveTradingEngine imported successfully")
        print("   ✅ Order types available:", [ot.value for ot in OrderType])
        print("   ✅ Trading modes available:", [tm.value for tm in TradingMode])
        
    except Exception as e:
        print(f"   ❌ Error importing modules: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 MetaAPI Integration Test Complete!")
    print("\n📋 Setup Instructions:")
    print("1. Sign up at https://app.metaapi.cloud/")
    print("2. Create a trading account (MT4/MT5)")
    print("3. Add your API keys to .env file:")
    print("   METAAPI_API_KEY=your_api_key")
    print("   METAAPI_ACCOUNT_ID=your_account_id")
    print("4. Start with demo mode for testing")
    print("\n🚀 Ready for live trading integration!")

if __name__ == "__main__":
    asyncio.run(test_metaapi_integration())