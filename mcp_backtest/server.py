"""
Main MCP Server for backtesting
"""

import asyncio
import json
import logging
import pandas as pd
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource,
    LoggingLevel
)

from .core.models import (
    BacktestRequest, BacktestResult, DataSourceConfig, 
    StrategyConfig, LLMConfig, BacktestConfig, MarketType,
    DataFormat, LLMProvider
)
from .core.backtest import BacktestEngine
from .data.handlers import DataHandler
from .strategies.base import StrategyManager
from .llm.providers import LLMManager
from .trading.live_engine import LiveTradingEngine, TradingMode
from .trading.metaapi_client import MetaAPIClient


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPBacktestServer:
    """Main MCP Backtest Server"""
    
    def __init__(self):
        self.server = Server("mcp-backtest")
        self.data_handler = DataHandler()
        self.strategy_manager = StrategyManager()
        self.llm_manager = LLMManager()
        
        # Storage for results
        self.results_storage: Dict[str, BacktestResult] = {}
        
        # Live trading sessions
        self.trading_sessions: Dict[str, LiveTradingEngine] = {}
        
        self._setup_tools()
        self._setup_handlers()
    
    def _setup_tools(self):
        """Setup MCP tools"""
        
        # Import strategy generator
        from .strategies.generator import StrategyGenerator
        self.strategy_generator = StrategyGenerator(self.llm_manager)
        
        # Tool for running backtest with CSV data
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="smart_backtest",
                    description="Smart backtesting with data source and trading prompt. MCP will intelligently parse data and generate strategy.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data_source": {"type": "string", "description": "Path to CSV file, JSON file, or API endpoint URL"},
                            "trading_prompt": {"type": "string", "description": "Describe your trading strategy requirements, goals, and preferences"},
                            "llm_provider": {"type": "string", "enum": ["openai", "gemini", "claude", "cloudflare", "qwen", "deepseek"], "default": "openai"},
                            "llm_model": {"type": "string", "description": "LLM model name", "default": "gpt-3.5-turbo"},
                            "initial_capital": {"type": "number", "description": "Initial capital", "default": 10000},
                            "commission": {"type": "number", "description": "Commission rate", "default": 0.001}
                        },
                        "required": ["data_source", "trading_prompt"]
                    }
                ),
                Tool(
                    name="get_backtest_results",
                    description="Get backtest results by test ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_id": {"type": "string", "description": "Test ID"}
                        },
                        "required": ["test_id"]
                    }
                ),
                Tool(
                    name="analyze_data",
                    description="Analyze market data from any source with intelligent parsing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data_source": {"type": "string", "description": "Path to CSV file, JSON file, or API endpoint URL"},
                            "analysis_prompt": {"type": "string", "description": "What specific analysis do you want? (trends, patterns, risks, etc.)"},
                            "llm_provider": {"type": "string", "enum": ["openai", "gemini", "claude", "cloudflare", "qwen", "deepseek"], "default": "openai"},
                            "llm_model": {"type": "string", "description": "LLM model name", "default": "gpt-3.5-turbo"}
                        },
                        "required": ["data_source", "analysis_prompt"]
                    }
                ),
                Tool(
                    name="start_live_trading",
                    description="Start live trading with MetaAPI using AI-generated strategy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbols": {"type": "array", "items": {"type": "string"}, "description": "Trading symbols (e.g., EURUSD, GBPUSD)"},
                            "trading_prompt": {"type": "string", "description": "Describe your trading strategy requirements"},
                            "mode": {"type": "string", "enum": ["demo", "live", "paper"], "default": "demo"},
                            "llm_provider": {"type": "string", "enum": ["openai", "gemini", "claude", "cloudflare", "qwen", "deepseek"], "default": "openai"},
                            "llm_model": {"type": "string", "description": "LLM model name", "default": "gpt-3.5-turbo"}
                        },
                        "required": ["symbols", "trading_prompt"]
                    }
                ),
                Tool(
                    name="stop_live_trading",
                    description="Stop live trading session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Trading session ID"}
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="get_trading_status",
                    description="Get current live trading status and performance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Trading session ID"}
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="get_account_info",
                    description="Get MetaAPI account information and balance",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
    
    def _setup_handlers(self):
        """Setup MCP handlers"""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "smart_backtest":
                    return await self._smart_backtest(arguments)
                elif name == "get_backtest_results":
                    return await self._get_backtest_results(arguments)
                elif name == "analyze_data":
                    return await self._analyze_data(arguments)
                elif name == "start_live_trading":
                    return await self._start_live_trading(arguments)
                elif name == "stop_live_trading":
                    return await self._stop_live_trading(arguments)
                elif name == "get_trading_status":
                    return await self._get_trading_status(arguments)
                elif name == "get_account_info":
                    return await self._get_account_info(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _smart_backtest(self, args: Dict[str, Any]) -> List[TextContent]:
        """Smart backtesting with intelligent data parsing and strategy generation"""
        try:
            # Step 1: Load and parse data intelligently
            data_source = args["data_source"]
            df, metadata = self.data_handler.load_data(data_source)
            
            # Step 2: Detect market information
            market_info = self.data_handler.detect_market_info(df, metadata)
            
            # Step 3: Create market data object
            market_data = self._create_market_data(df, market_info, metadata)
            
            # Step 4: Create LLM config with defaults
            llm_config = LLMConfig(
                provider=LLMProvider(args.get("llm_provider", "openai")),
                model_name=args.get("llm_model", "gpt-3.5-turbo")
            )
            
            # Step 5: Generate strategy from user prompt
            strategy_impl = await self.strategy_generator.generate_strategy_from_prompt(
                market_data, args["trading_prompt"], llm_config
            )
            
            # Step 6: Run backtest with generated strategy
            result = await self._execute_smart_backtest(
                market_data, 
                strategy_impl, 
                llm_config,
                args.get("initial_capital", 10000),
                args.get("commission", 0.001)
            )
            
            # Step 7: Store result
            self.results_storage[result.test_id] = result
            
            return [TextContent(
                type="text",
                text=f"🚀 Smart Backtest Completed Successfully!\n\n"
                     f"📊 Data Analysis:\n"
                     f"- Source: {data_source}\n"
                     f"- Market Type: {market_info.get('market_type', 'unknown').title()}\n"
                     f"- Data Points: {len(df)}\n"
                     f"- Date Range: {metadata.get('date_range', {}).get('start', 'N/A')} to {metadata.get('date_range', {}).get('end', 'N/A')}\n\n"
                     f"🤖 AI Generated Strategy:\n"
                     f"- Strategy: {strategy_impl.get('strategy_name', 'Custom Strategy')}\n"
                     f"- Description: {strategy_impl.get('description', 'AI-generated strategy')}\n\n"
                     f"📈 Backtest Results:\n"
                     f"- Test ID: {result.test_id}\n"
                     f"- Total Return: {result.metrics.get('total_return', 0)*100:.2f}%\n"
                     f"- Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}\n"
                     f"- Max Drawdown: {result.metrics.get('max_drawdown', 0)*100:.2f}%\n"
                     f"- Total Trades: {result.metrics.get('total_trades', 0)}\n"
                     f"- Win Rate: {result.metrics.get('win_rate', 0)*100:.2f}%\n\n"
                     f"🔍 AI Analysis:\n{result.analysis}\n\n"
                     f"📋 Comprehensive Results:\n{json.dumps(result.result_matrix, indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error in smart backtest: {str(e)}")
            return [TextContent(type="text", text=f"Error running smart backtest: {str(e)}")]
    
    async def _analyze_data(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze market data with intelligent parsing"""
        try:
            # Step 1: Load and parse data intelligently
            data_source = args["data_source"]
            df, metadata = self.data_handler.load_data(data_source)
            
            # Step 2: Detect market information
            market_info = self.data_handler.detect_market_info(df, metadata)
            
            # Step 3: Create market data object
            market_data = self._create_market_data(df, market_info, metadata)
            
            # Step 4: Create LLM config
            llm_config = LLMConfig(
                provider=LLMProvider(args.get("llm_provider", "openai")),
                model_name=args.get("llm_model", "gpt-3.5-turbo")
            )
            
            # Step 5: Get LLM provider and analyze
            llm_provider = self.llm_manager.get_provider(llm_config.provider, llm_config)
            analysis = await llm_provider.generate_analysis(market_data, args["analysis_prompt"])
            
            return [TextContent(
                type="text",
                text=f"📊 Data Analysis Complete!\n\n"
                     f"📈 Data Overview:\n"
                     f"- Source: {data_source}\n"
                     f"- Market Type: {market_info.get('market_type', 'unknown').title()}\n"
                     f"- Data Points: {len(df)}\n"
                     f"- Date Range: {metadata.get('date_range', {}).get('start', 'N/A')} to {metadata.get('date_range', {}).get('end', 'N/A')}\n"
                     f"- Columns: {', '.join(df.columns)}\n"
                     f"- Has Headers: {metadata.get('had_header', 'N/A')}\n\n"
                     f"🤖 AI Analysis:\n{analysis}\n\n"
                     f"📋 Data Statistics:\n{json.dumps(market_info.get('characteristics', {}), indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error in data analysis: {str(e)}")
            return [TextContent(type="text", text=f"Error analyzing data: {str(e)}")]
    
    async def _get_backtest_results(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get backtest results by test ID"""
        test_id = args["test_id"]
        
        if test_id not in self.results_storage:
            return [TextContent(type="text", text=f"Test ID {test_id} not found")]
        
        result = self.results_storage[test_id]
        
        return [TextContent(
            type="text",
            text=f"📊 Backtest Results for {test_id}\n\n"
                 f"🎯 Strategy: {result.request.strategy.strategy_name if hasattr(result, 'request') else 'AI Generated'}\n"
                 f"📈 Market: {result.request.market_type if hasattr(result, 'request') else 'Auto-detected'}\n"
                 f"📅 Created: {result.created_at}\n\n"
                 f"📊 Performance Metrics:\n"
                 f"- Total Return: {result.metrics.get('total_return', 0)*100:.2f}%\n"
                 f"- Annualized Return: {result.metrics.get('annualized_return', 0)*100:.2f}%\n"
                 f"- Volatility: {result.metrics.get('volatility', 0)*100:.2f}%\n"
                 f"- Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}\n"
                 f"- Max Drawdown: {result.metrics.get('max_drawdown', 0)*100:.2f}%\n"
                 f"- Total Trades: {result.metrics.get('total_trades', 0)}\n"
                 f"- Win Rate: {result.metrics.get('win_rate', 0)*100:.2f}%\n"
                 f"- Profit Factor: {result.metrics.get('profit_factor', 0):.2f}\n\n"
                 f"🤖 AI Analysis:\n{result.analysis}\n\n"
                 f"📋 Comprehensive Results:\n{json.dumps(result.result_matrix, indent=2)}"
        )]
    
    def _create_market_data(self, df: pd.DataFrame, market_info: Dict[str, Any], metadata: Dict[str, Any]):
        """Create MarketData object from DataFrame"""
        from .core.models import MarketData, MarketType
        
        # Convert market type string to enum
        market_type_map = {
            'crypto': MarketType.CRYPTO,
            'stock': MarketType.STOCK,
            'forex': MarketType.FOREX,
            'unknown': MarketType.CRYPTO  # Default to crypto
        }
        
        market_type = market_type_map.get(market_info.get('market_type', 'unknown'), MarketType.CRYPTO)
        
        return MarketData(
            symbol=market_info.get('symbol', 'UNKNOWN'),
            market_type=market_type,
            data=df,
            metadata=metadata
        )
    
    async def _execute_smart_backtest(
        self, 
        market_data, 
        strategy_impl: Dict[str, Any], 
        llm_config: LLMConfig,
        initial_capital: float,
        commission: float
    ):
        """Execute backtest with AI-generated strategy"""
        from .core.models import BacktestRequest, StrategyConfig, BacktestConfig, DataSourceConfig, DataFormat
        
        # Create configs
        data_source = DataSourceConfig(
            source_type=DataFormat.CSV,  # Will be overridden by the engine
            source_path="dynamic"
        )
        
        strategy_config = StrategyConfig(
            strategy_name=strategy_impl["strategy_name"],
            parameters=strategy_impl.get("parameters", {}),
            risk_management={}
        )
        
        backtest_config = BacktestConfig(
            initial_capital=initial_capital,
            commission=commission
        )
        
        # Create request
        request = BacktestRequest(
            data_source=data_source,
            market_type=market_data.market_type,
            strategy=strategy_config,
            backtest_config=backtest_config,
            llm_config=llm_config,
            analysis_requirements=[]
        )
        
        # Execute backtest with the engine
        engine = BacktestEngine()
        result = await engine.run_backtest(request, market_data)
        
        return result
    
    async def _start_live_trading(self, args: Dict[str, Any]) -> List[TextContent]:
        """Start live trading with MetaAPI"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create LLM config
            llm_config = LLMConfig(
                provider=LLMProvider(args.get("llm_provider", "openai")),
                model_name=args.get("llm_model", "gpt-3.5-turbo")
            )
            
            # Generate strategy from prompt
            symbols = args["symbols"]
            trading_prompt = args["trading_prompt"]
            mode = TradingMode(args.get("mode", "demo"))
            
            # Create sample market data for strategy generation
            # In practice, this would use real market data
            sample_data = pd.DataFrame({
                'open': [1.0] * 100,
                'high': [1.1] * 100,
                'low': [0.9] * 100,
                'close': [1.0] * 100,
                'volume': [1000] * 100
            })
            
            # Generate strategy
            strategy_impl = await self.strategy_generator.generate_strategy_from_prompt(
                sample_data, trading_prompt, llm_config
            )
            
            # Create strategy instance
            strategy = self.strategy_manager.create_strategy(
                strategy_impl.get("strategy_name", "custom"),
                strategy_impl.get("params", {})
            )
            
            # Create and start live trading engine
            trading_engine = LiveTradingEngine(
                strategy=strategy,
                symbols=symbols,
                mode=mode
            )
            
            # Store session
            self.trading_sessions[session_id] = trading_engine
            
            # Start trading (in background)
            asyncio.create_task(trading_engine.start())
            
            return [TextContent(
                type="text",
                text=f"🚀 Live Trading Started Successfully!\n\n"
                     f"📋 Session Details:\n"
                     f"- Session ID: {session_id}\n"
                     f"- Mode: {mode.value.upper()}\n"
                     f"- Symbols: {', '.join(symbols)}\n"
                     f"- Strategy: {strategy_impl.get('strategy_name', 'Custom Strategy')}\n\n"
                     f"🤖 AI Generated Strategy:\n"
                     f"- Description: {strategy_impl.get('description', 'AI-generated strategy')}\n"
                     f"- Parameters: {json.dumps(strategy_impl.get('params', {}), indent=2)}\n\n"
                     f"⚠️ Important:\n"
                     f"- This is {mode.value.upper()} mode\n"
                     f"- Monitor your trades regularly\n"
                     f"- Use 'get_trading_status' to check performance\n"
                     f"- Use 'stop_live_trading' to stop when needed\n\n"
                     f"📊 Use session ID '{session_id}' to monitor this trading session."
            )]
            
        except Exception as e:
            logger.error(f"Error starting live trading: {str(e)}")
            return [TextContent(type="text", text=f"Error starting live trading: {str(e)}")]
    
    async def _stop_live_trading(self, args: Dict[str, Any]) -> List[TextContent]:
        """Stop live trading session"""
        try:
            session_id = args["session_id"]
            
            if session_id not in self.trading_sessions:
                return [TextContent(type="text", text=f"Trading session {session_id} not found")]
            
            trading_engine = self.trading_sessions[session_id]
            await trading_engine.stop()
            
            # Get final status
            status = trading_engine.get_status()
            
            # Remove session
            del self.trading_sessions[session_id]
            
            return [TextContent(
                type="text",
                text=f"🛑 Live Trading Stopped Successfully!\n\n"
                     f"📋 Final Session Summary:\n"
                     f"- Session ID: {session_id}\n"
                     f"- Total Trades: {status.get('trades_today', 0)}\n"
                     f"- Daily P&L: ${status.get('daily_pnl', 0):.2f}\n"
                     f"- Open Positions: {status.get('positions', 0)}\n"
                     f"- Pending Orders: {status.get('orders', 0)}\n\n"
                     f"✅ All positions and orders have been handled according to your risk management settings."
            )]
            
        except Exception as e:
            logger.error(f"Error stopping live trading: {str(e)}")
            return [TextContent(type="text", text=f"Error stopping live trading: {str(e)}")]
    
    async def _get_trading_status(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get current trading status"""
        try:
            session_id = args["session_id"]
            
            if session_id not in self.trading_sessions:
                return [TextContent(type="text", text=f"Trading session {session_id} not found")]
            
            trading_engine = self.trading_sessions[session_id]
            status = trading_engine.get_status()
            
            return [TextContent(
                type="text",
                text=f"📊 Live Trading Status Report\n\n"
                     f"📋 Session: {session_id}\n"
                     f"- State: {status.get('state', 'unknown').upper()}\n"
                     f"- Symbols: {', '.join(status.get('symbols', []))}\n\n"
                     f"📈 Performance:\n"
                     f"- Daily P&L: ${status.get('daily_pnl', 0):.2f}\n"
                     f"- Total Trades Today: {status.get('trades_today', 0)}\n\n"
                     f"📊 Current Positions:\n"
                     f"- Open Positions: {status.get('positions', 0)}\n"
                     f"- Pending Orders: {status.get('orders', 0)}\n\n"
                     f"🎯 Latest Signals:\n"
                     f"{json.dumps(status.get('last_signals', {}), indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error getting trading status: {str(e)}")
            return [TextContent(type="text", text=f"Error getting trading status: {str(e)}")]
    
    async def _get_account_info(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get MetaAPI account information"""
        try:
            async with MetaAPIClient() as client:
                account_info = await client.get_account_info()
                equity = await client.get_account_equity()
                balance = await client.get_account_balance()
                margin = await client.get_account_margin()
                free_margin = await client.get_free_margin()
                
                positions = await client.get_positions()
                orders = await client.get_orders()
                
                return [TextContent(
                    type="text",
                    text=f"💰 MetaAPI Account Information\n\n"
                         f"📊 Account Details:\n"
                         f"- Account ID: {account_info.get('login', 'N/A')}\n"
                         f"- Server: {account_info.get('server', 'N/A')}\n"
                         f"- Currency: {account_info.get('currency', 'N/A')}\n"
                         f"- Leverage: {account_info.get('leverage', 'N/A')}\n\n"
                         f"💵 Account Balance:\n"
                         f"- Balance: ${balance:.2f}\n"
                         f"- Equity: ${equity:.2f}\n"
                         f"- Margin Used: ${margin:.2f}\n"
                         f"- Free Margin: ${free_margin:.2f}\n\n"
                         f"📈 Trading Status:\n"
                         f"- Open Positions: {len(positions)}\n"
                         f"- Pending Orders: {len(orders)}\n\n"
                         f"📋 Positions:\n"
                         f"{json.dumps([pos.to_dict() for pos in positions], indent=2)}"
                )]
                
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return [TextContent(type="text", text=f"Error getting account info: {str(e)}")]
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


async def main():
    """Main entry point"""
    server = MCPBacktestServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())