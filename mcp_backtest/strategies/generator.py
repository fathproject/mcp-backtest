"""
AI-powered strategy generator that creates custom trading strategies based on user prompts
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from ..core.models import MarketData, LLMConfig
from ..llm.providers import LLMManager
import json
import logging

logger = logging.getLogger(__name__)


class StrategyGenerator:
    """Generates custom trading strategies using AI based on user prompts"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        
    async def generate_strategy_from_prompt(
        self, 
        market_data: MarketData, 
        user_prompt: str,
        llm_config: LLMConfig
    ) -> Dict[str, Any]:
        """
        Generate a custom trading strategy based on user prompt
        
        Args:
            market_data: The market data to analyze
            user_prompt: User's description of desired strategy
            llm_config: LLM configuration
            
        Returns:
            Dictionary containing strategy implementation and parameters
        """
        try:
            # Get LLM provider
            llm_provider = self.llm_manager.get_provider(llm_config.provider, llm_config)
            
            # Prepare data analysis
            data_analysis = await self._analyze_market_data(market_data, llm_provider)
            
            # Generate strategy based on prompt
            strategy_spec = await self._generate_strategy_specification(
                market_data, user_prompt, data_analysis, llm_provider
            )
            
            # Convert specification to executable strategy
            strategy_implementation = await self._create_strategy_implementation(
                strategy_spec, llm_provider
            )
            
            return strategy_implementation
            
        except Exception as e:
            logger.error(f"Error generating strategy: {str(e)}")
            raise
    
    async def _analyze_market_data(self, market_data: MarketData, llm_provider) -> str:
        """Analyze market data to understand characteristics"""
        context = f"""
        Analyze this {market_data.market_type} market data for {market_data.symbol}.
        Focus on:
        - Market volatility patterns
        - Price trends and momentum
        - Volume characteristics
        - Best indicators for this market
        - Risk characteristics
        
        Provide a concise technical analysis.
        """
        
        return await llm_provider.generate_analysis(market_data, context)
    
    async def _generate_strategy_specification(
        self, 
        market_data: MarketData, 
        user_prompt: str,
        data_analysis: str,
        llm_provider
    ) -> Dict[str, Any]:
        """Generate strategy specification based on user prompt"""
        
        prompt = f"""
        Based on the following market analysis and user requirements, create a detailed trading strategy specification:
        
        MARKET ANALYSIS:
        {data_analysis}
        
        USER REQUIREMENTS:
        {user_prompt}
        
        MARKET INFO:
        - Type: {market_data.market_type}
        - Symbol: {market_data.symbol}
        - Data Period: {len(market_data.data)} periods
        
        Create a trading strategy that addresses the user's requirements. Return a JSON specification with:
        {{
            "strategy_name": "Custom strategy name",
            "strategy_type": "trend_following|mean_reversion|momentum|arbitrage|custom",
            "description": "Clear description of the strategy",
            "entry_conditions": [
                "Specific condition 1",
                "Specific condition 2"
            ],
            "exit_conditions": [
                "Specific exit condition 1",
                "Specific exit condition 2"
            ],
            "indicators": [
                {{"name": "indicator_name", "params": {{"param1": value1}}}},
                {{"name": "indicator_name2", "params": {{"param1": value1}}}}
            ],
            "risk_management": {{
                "stop_loss": "percentage or fixed amount",
                "take_profit": "percentage or fixed amount",
                "position_size": "percentage of capital"
            }},
            "parameters": {{
                "key_parameter1": "value1",
                "key_parameter2": "value2"
            }}
        }}
        
        Make sure the strategy is practical and addresses the user's specific requirements.
        """
        
        response = await llm_provider.generate_strategy(market_data, prompt)
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                strategy_spec = json.loads(json_match.group())
            else:
                # If no JSON found, create a basic structure
                strategy_spec = {
                    "strategy_name": "Custom Strategy",
                    "strategy_type": "custom",
                    "description": response,
                    "entry_conditions": ["Buy when conditions are met"],
                    "exit_conditions": ["Sell when conditions are met"],
                    "indicators": [],
                    "risk_management": {
                        "stop_loss": "5%",
                        "take_profit": "10%",
                        "position_size": "100%"
                    },
                    "parameters": {}
                }
        except json.JSONDecodeError:
            # Fallback strategy specification
            strategy_spec = {
                "strategy_name": "AI Generated Strategy",
                "strategy_type": "custom",
                "description": response,
                "entry_conditions": ["Custom entry logic"],
                "exit_conditions": ["Custom exit logic"],
                "indicators": [],
                "risk_management": {
                    "stop_loss": "5%",
                    "take_profit": "10%",
                    "position_size": "100%"
                },
                "parameters": {}
            }
        
        return strategy_spec
    
    async def _create_strategy_implementation(
        self, 
        strategy_spec: Dict[str, Any], 
        llm_provider
    ) -> Dict[str, Any]:
        """Create executable strategy implementation"""
        
        # Map strategy types to implementation
        strategy_type = strategy_spec.get("strategy_type", "custom")
        
        if strategy_type == "trend_following":
            return self._create_trend_following_strategy(strategy_spec)
        elif strategy_type == "mean_reversion":
            return self._create_mean_reversion_strategy(strategy_spec)
        elif strategy_type == "momentum":
            return self._create_momentum_strategy(strategy_spec)
        else:
            return self._create_adaptive_strategy(strategy_spec)
    
    def _create_trend_following_strategy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create trend following strategy implementation"""
        return {
            "strategy_name": "moving_average_crossover",
            "parameters": {
                "short_window": 20,
                "long_window": 50,
                "stop_loss": 0.05,
                "take_profit": 0.15
            },
            "description": spec.get("description", "Trend following strategy"),
            "specification": spec
        }
    
    def _create_mean_reversion_strategy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create mean reversion strategy implementation"""
        return {
            "strategy_name": "mean_reversion",
            "parameters": {
                "lookback_period": 20,
                "std_dev_threshold": 2.0,
                "stop_loss": 0.03,
                "take_profit": 0.06
            },
            "description": spec.get("description", "Mean reversion strategy"),
            "specification": spec
        }
    
    def _create_momentum_strategy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create momentum strategy implementation"""
        return {
            "strategy_name": "momentum",
            "parameters": {
                "momentum_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "stop_loss": 0.04,
                "take_profit": 0.12
            },
            "description": spec.get("description", "Momentum strategy"),
            "specification": spec
        }
    
    def _create_adaptive_strategy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create adaptive strategy based on specification"""
        # Extract parameters from specification
        risk_mgmt = spec.get("risk_management", {})
        
        # Parse stop loss and take profit
        stop_loss = self._parse_percentage(risk_mgmt.get("stop_loss", "5%"))
        take_profit = self._parse_percentage(risk_mgmt.get("take_profit", "10%"))
        
        # Choose base strategy based on indicators mentioned
        indicators = spec.get("indicators", [])
        indicator_names = [ind.get("name", "").lower() for ind in indicators]
        
        if any("rsi" in name for name in indicator_names):
            base_strategy = "rsi"
            parameters = {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70
            }
        elif any("ma" in name or "moving" in name for name in indicator_names):
            base_strategy = "moving_average_crossover"
            parameters = {
                "short_window": 20,
                "long_window": 50
            }
        else:
            # Default to buy and hold for simple strategies
            base_strategy = "buy_and_hold"
            parameters = {}
        
        parameters.update({
            "stop_loss": stop_loss,
            "take_profit": take_profit
        })
        
        return {
            "strategy_name": base_strategy,
            "parameters": parameters,
            "description": spec.get("description", "AI-generated custom strategy"),
            "specification": spec
        }
    
    def _parse_percentage(self, value: str) -> float:
        """Parse percentage string to float"""
        if isinstance(value, str):
            if "%" in value:
                return float(value.replace("%", "")) / 100
            else:
                return float(value)
        return float(value)