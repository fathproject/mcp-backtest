"""
Main MCP Server for backtesting
"""

import asyncio
import json
import logging
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
        
        self._setup_tools()
        self._setup_handlers()
    
    def _setup_tools(self):
        """Setup MCP tools"""
        
        # Tool for running backtest with CSV data
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="run_backtest_csv",
                    description="Run backtest with CSV data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "csv_path": {"type": "string", "description": "Path to CSV file"},
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "market_type": {"type": "string", "enum": ["crypto", "stock", "forex"]},
                            "strategy_name": {"type": "string", "description": "Strategy name"},
                            "strategy_params": {"type": "object", "description": "Strategy parameters"},
                            "llm_provider": {"type": "string", "enum": ["openai", "gemini", "claude", "cloudflare", "qwen", "deepseek"]},
                            "llm_model": {"type": "string", "description": "LLM model name"},
                            "initial_capital": {"type": "number", "description": "Initial capital", "default": 10000},
                            "commission": {"type": "number", "description": "Commission rate", "default": 0.001},
                            "analysis_requirements": {"type": "array", "items": {"type": "string"}, "description": "Analysis requirements"}
                        },
                        "required": ["csv_path", "symbol", "market_type", "strategy_name", "llm_provider", "llm_model"]
                    }
                ),
                Tool(
                    name="run_backtest_json",
                    description="Run backtest with JSON data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "json_path": {"type": "string", "description": "Path to JSON file"},
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "market_type": {"type": "string", "enum": ["crypto", "stock", "forex"]},
                            "strategy_name": {"type": "string", "description": "Strategy name"},
                            "strategy_params": {"type": "object", "description": "Strategy parameters"},
                            "llm_provider": {"type": "string", "enum": ["openai", "gemini", "claude", "cloudflare", "qwen", "deepseek"]},
                            "llm_model": {"type": "string", "description": "LLM model name"},
                            "initial_capital": {"type": "number", "description": "Initial capital", "default": 10000},
                            "commission": {"type": "number", "description": "Commission rate", "default": 0.001},
                            "analysis_requirements": {"type": "array", "items": {"type": "string"}, "description": "Analysis requirements"}
                        },
                        "required": ["json_path", "symbol", "market_type", "strategy_name", "llm_provider", "llm_model"]
                    }
                ),
                Tool(
                    name="run_backtest_api",
                    description="Run backtest with API data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_endpoint": {"type": "string", "description": "API endpoint URL"},
                            "api_headers": {"type": "object", "description": "API headers"},
                            "api_params": {"type": "object", "description": "API parameters"},
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "market_type": {"type": "string", "enum": ["crypto", "stock", "forex"]},
                            "strategy_name": {"type": "string", "description": "Strategy name"},
                            "strategy_params": {"type": "object", "description": "Strategy parameters"},
                            "llm_provider": {"type": "string", "enum": ["openai", "gemini", "claude", "cloudflare", "qwen", "deepseek"]},
                            "llm_model": {"type": "string", "description": "LLM model name"},
                            "initial_capital": {"type": "number", "description": "Initial capital", "default": 10000},
                            "commission": {"type": "number", "description": "Commission rate", "default": 0.001},
                            "analysis_requirements": {"type": "array", "items": {"type": "string"}, "description": "Analysis requirements"}
                        },
                        "required": ["api_endpoint", "symbol", "market_type", "strategy_name", "llm_provider", "llm_model"]
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
                    name="list_strategies",
                    description="List available trading strategies",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="analyze_market_data",
                    description="Analyze market data using LLM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data_path": {"type": "string", "description": "Path to data file"},
                            "data_format": {"type": "string", "enum": ["csv", "json"]},
                            "market_type": {"type": "string", "enum": ["crypto", "stock", "forex"]},
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "llm_provider": {"type": "string", "enum": ["openai", "gemini", "claude", "cloudflare", "qwen", "deepseek"]},
                            "llm_model": {"type": "string", "description": "LLM model name"},
                            "context": {"type": "string", "description": "Analysis context"}
                        },
                        "required": ["data_path", "data_format", "market_type", "symbol", "llm_provider", "llm_model"]
                    }
                )
            ]
    
    def _setup_handlers(self):
        """Setup MCP handlers"""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "run_backtest_csv":
                    return await self._run_backtest_csv(arguments)
                elif name == "run_backtest_json":
                    return await self._run_backtest_json(arguments)
                elif name == "run_backtest_api":
                    return await self._run_backtest_api(arguments)
                elif name == "get_backtest_results":
                    return await self._get_backtest_results(arguments)
                elif name == "list_strategies":
                    return await self._list_strategies()
                elif name == "analyze_market_data":
                    return await self._analyze_market_data(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _run_backtest_csv(self, args: Dict[str, Any]) -> List[TextContent]:
        """Run backtest with CSV data"""
        try:
            # Create data source config
            data_source = DataSourceConfig(
                source_type=DataFormat.CSV,
                source_path=args["csv_path"]
            )
            
            # Create strategy config
            strategy_config = StrategyConfig(
                strategy_name=args["strategy_name"],
                parameters=args.get("strategy_params", {}),
                risk_management={}
            )
            
            # Create LLM config
            llm_config = LLMConfig(
                provider=LLMProvider(args["llm_provider"]),
                model_name=args["llm_model"]
            )
            
            # Create backtest config
            backtest_config = BacktestConfig(
                initial_capital=args.get("initial_capital", 10000),
                commission=args.get("commission", 0.001)
            )
            
            # Create request
            request = BacktestRequest(
                data_source=data_source,
                market_type=MarketType(args["market_type"]),
                strategy=strategy_config,
                backtest_config=backtest_config,
                llm_config=llm_config,
                analysis_requirements=args.get("analysis_requirements", [])
            )
            
            # Run backtest
            result = await self._execute_backtest(request, args["symbol"])
            
            # Store result
            self.results_storage[result.test_id] = result
            
            return [TextContent(
                type="text",
                text=f"Backtest completed successfully!\n\n"
                     f"Test ID: {result.test_id}\n"
                     f"Total Return: {result.metrics.get('total_return', 0)*100:.2f}%\n"
                     f"Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}\n"
                     f"Max Drawdown: {result.metrics.get('max_drawdown', 0)*100:.2f}%\n"
                     f"Total Trades: {result.metrics.get('total_trades', 0)}\n"
                     f"Win Rate: {result.metrics.get('win_rate', 0)*100:.2f}%\n\n"
                     f"Analysis:\n{result.analysis}\n\n"
                     f"Result Matrix:\n{json.dumps(result.result_matrix, indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error in CSV backtest: {str(e)}")
            return [TextContent(type="text", text=f"Error running backtest: {str(e)}")]
    
    async def _run_backtest_json(self, args: Dict[str, Any]) -> List[TextContent]:
        """Run backtest with JSON data"""
        try:
            # Create data source config
            data_source = DataSourceConfig(
                source_type=DataFormat.JSON,
                source_path=args["json_path"]
            )
            
            # Create strategy config
            strategy_config = StrategyConfig(
                strategy_name=args["strategy_name"],
                parameters=args.get("strategy_params", {}),
                risk_management={}
            )
            
            # Create LLM config
            llm_config = LLMConfig(
                provider=LLMProvider(args["llm_provider"]),
                model_name=args["llm_model"]
            )
            
            # Create backtest config
            backtest_config = BacktestConfig(
                initial_capital=args.get("initial_capital", 10000),
                commission=args.get("commission", 0.001)
            )
            
            # Create request
            request = BacktestRequest(
                data_source=data_source,
                market_type=MarketType(args["market_type"]),
                strategy=strategy_config,
                backtest_config=backtest_config,
                llm_config=llm_config,
                analysis_requirements=args.get("analysis_requirements", [])
            )
            
            # Run backtest
            result = await self._execute_backtest(request, args["symbol"])
            
            # Store result
            self.results_storage[result.test_id] = result
            
            return [TextContent(
                type="text",
                text=f"Backtest completed successfully!\n\n"
                     f"Test ID: {result.test_id}\n"
                     f"Total Return: {result.metrics.get('total_return', 0)*100:.2f}%\n"
                     f"Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}\n"
                     f"Max Drawdown: {result.metrics.get('max_drawdown', 0)*100:.2f}%\n"
                     f"Total Trades: {result.metrics.get('total_trades', 0)}\n"
                     f"Win Rate: {result.metrics.get('win_rate', 0)*100:.2f}%\n\n"
                     f"Analysis:\n{result.analysis}\n\n"
                     f"Result Matrix:\n{json.dumps(result.result_matrix, indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error in JSON backtest: {str(e)}")
            return [TextContent(type="text", text=f"Error running backtest: {str(e)}")]
    
    async def _run_backtest_api(self, args: Dict[str, Any]) -> List[TextContent]:
        """Run backtest with API data"""
        try:
            # Create data source config
            data_source = DataSourceConfig(
                source_type=DataFormat.API,
                api_endpoint=args["api_endpoint"],
                api_headers=args.get("api_headers", {}),
                api_params=args.get("api_params", {})
            )
            
            # Create strategy config
            strategy_config = StrategyConfig(
                strategy_name=args["strategy_name"],
                parameters=args.get("strategy_params", {}),
                risk_management={}
            )
            
            # Create LLM config
            llm_config = LLMConfig(
                provider=LLMProvider(args["llm_provider"]),
                model_name=args["llm_model"]
            )
            
            # Create backtest config
            backtest_config = BacktestConfig(
                initial_capital=args.get("initial_capital", 10000),
                commission=args.get("commission", 0.001)
            )
            
            # Create request
            request = BacktestRequest(
                data_source=data_source,
                market_type=MarketType(args["market_type"]),
                strategy=strategy_config,
                backtest_config=backtest_config,
                llm_config=llm_config,
                analysis_requirements=args.get("analysis_requirements", [])
            )
            
            # Run backtest
            result = await self._execute_backtest(request, args["symbol"])
            
            # Store result
            self.results_storage[result.test_id] = result
            
            return [TextContent(
                type="text",
                text=f"Backtest completed successfully!\n\n"
                     f"Test ID: {result.test_id}\n"
                     f"Total Return: {result.metrics.get('total_return', 0)*100:.2f}%\n"
                     f"Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}\n"
                     f"Max Drawdown: {result.metrics.get('max_drawdown', 0)*100:.2f}%\n"
                     f"Total Trades: {result.metrics.get('total_trades', 0)}\n"
                     f"Win Rate: {result.metrics.get('win_rate', 0)*100:.2f}%\n\n"
                     f"Analysis:\n{result.analysis}\n\n"
                     f"Result Matrix:\n{json.dumps(result.result_matrix, indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error in API backtest: {str(e)}")
            return [TextContent(type="text", text=f"Error running backtest: {str(e)}")]
    
    async def _get_backtest_results(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get backtest results by test ID"""
        test_id = args["test_id"]
        
        if test_id not in self.results_storage:
            return [TextContent(type="text", text=f"Test ID {test_id} not found")]
        
        result = self.results_storage[test_id]
        
        return [TextContent(
            type="text",
            text=f"Backtest Results for {test_id}\n\n"
                 f"Strategy: {result.request.strategy.strategy_name}\n"
                 f"Market: {result.request.market_type}\n"
                 f"Created: {result.created_at}\n\n"
                 f"Performance Metrics:\n"
                 f"Total Return: {result.metrics.get('total_return', 0)*100:.2f}%\n"
                 f"Annualized Return: {result.metrics.get('annualized_return', 0)*100:.2f}%\n"
                 f"Volatility: {result.metrics.get('volatility', 0)*100:.2f}%\n"
                 f"Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}\n"
                 f"Max Drawdown: {result.metrics.get('max_drawdown', 0)*100:.2f}%\n"
                 f"Total Trades: {result.metrics.get('total_trades', 0)}\n"
                 f"Win Rate: {result.metrics.get('win_rate', 0)*100:.2f}%\n"
                 f"Profit Factor: {result.metrics.get('profit_factor', 0):.2f}\n\n"
                 f"Analysis:\n{result.analysis}\n\n"
                 f"Result Matrix:\n{json.dumps(result.result_matrix, indent=2)}"
        )]
    
    async def _list_strategies(self) -> List[TextContent]:
        """List available strategies"""
        strategies = self.strategy_manager.list_strategies()
        
        strategy_descriptions = {
            'buy_and_hold': 'Simple buy and hold strategy',
            'moving_average_crossover': 'Moving average crossover strategy',
            'rsi': 'RSI (Relative Strength Index) strategy',
            'mean_reversion': 'Mean reversion strategy using Bollinger Bands',
            'momentum': 'Momentum strategy based on price momentum'
        }
        
        text = "Available Trading Strategies:\n\n"
        for strategy in strategies:
            description = strategy_descriptions.get(strategy, 'No description available')
            text += f"• {strategy}: {description}\n"
        
        return [TextContent(type="text", text=text)]
    
    async def _analyze_market_data(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze market data using LLM"""
        try:
            # Load market data
            data_source = DataSourceConfig(
                source_type=DataFormat(args["data_format"]),
                source_path=args["data_path"]
            )
            
            market_data = await self.data_handler.load_data(
                data_source, 
                MarketType(args["market_type"]), 
                args["symbol"]
            )
            
            # Setup LLM
            llm_config = LLMConfig(
                provider=LLMProvider(args["llm_provider"]),
                model_name=args["llm_model"]
            )
            
            self.llm_manager.add_provider(llm_config)
            
            # Generate analysis
            context = args.get("context", "General market analysis")
            analysis = await self.llm_manager.generate_analysis(
                llm_config.provider, 
                market_data, 
                context
            )
            
            return [TextContent(
                type="text",
                text=f"Market Analysis for {args['symbol']} ({args['market_type']})\n\n"
                     f"Data Period: {market_data.data[0].timestamp} to {market_data.data[-1].timestamp}\n"
                     f"Data Points: {len(market_data.data)}\n\n"
                     f"Analysis:\n{analysis}"
            )]
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return [TextContent(type="text", text=f"Error analyzing market data: {str(e)}")]
    
    async def _execute_backtest(self, request: BacktestRequest, symbol: str) -> BacktestResult:
        """Execute complete backtest"""
        
        # Load market data
        market_data = await self.data_handler.load_data(
            request.data_source, 
            request.market_type, 
            symbol
        )
        
        # Validate and preprocess data
        if not self.data_handler.validate_data(market_data):
            raise ValueError("Invalid market data")
        
        market_data = self.data_handler.preprocess_data(market_data)
        
        # Get strategy and generate signals
        strategy = self.strategy_manager.get_strategy(request.strategy)
        signals = await strategy.generate_signals(market_data)
        
        # Run backtest
        engine = BacktestEngine(request.backtest_config)
        result = await engine.run_backtest(request, market_data, signals)
        
        # Setup LLM and generate analysis
        self.llm_manager.add_provider(request.llm_config)
        analysis = await self.llm_manager.analyze_results(
            request.llm_config.provider, 
            result
        )
        
        # Update result with analysis
        result.analysis = analysis
        
        return result
    
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