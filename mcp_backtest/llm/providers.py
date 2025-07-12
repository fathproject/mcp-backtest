"""
LLM integration for multiple AI providers
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import anthropic
except ImportError:
    anthropic = None

import aiohttp
from ..core.models import LLMConfig, LLMProvider, MarketData, BacktestResult


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key
        self.model_name = config.model_name
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
    
    @abstractmethod
    async def generate_analysis(self, market_data: MarketData, context: str) -> str:
        """Generate analysis based on market data"""
        pass
    
    @abstractmethod
    async def generate_strategy(self, market_data: MarketData, requirements: str) -> str:
        """Generate trading strategy"""
        pass
    
    @abstractmethod
    async def analyze_results(self, results: BacktestResult) -> str:
        """Analyze backtest results"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not openai:
            raise ImportError("OpenAI package not installed")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
    
    async def generate_analysis(self, market_data: MarketData, context: str) -> str:
        """Generate analysis using OpenAI GPT"""
        try:
            # Prepare market data summary
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Analyze the following {market_data.market_type} market data for {market_data.symbol}:
            
            {data_summary}
            
            Context: {context}
            
            Please provide a comprehensive analysis including:
            1. Market trends and patterns
            2. Price action analysis
            3. Volume analysis (if available)
            4. Technical indicators insights
            5. Risk assessment
            6. Trading opportunities
            
            Format the response in a clear, structured manner.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst specializing in market analysis and trading strategies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating analysis: {str(e)}"
    
    async def generate_strategy(self, market_data: MarketData, requirements: str) -> str:
        """Generate trading strategy using OpenAI GPT"""
        try:
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Based on the following {market_data.market_type} market data for {market_data.symbol}:
            
            {data_summary}
            
            Requirements: {requirements}
            
            Please generate a detailed trading strategy that includes:
            1. Entry and exit criteria
            2. Risk management rules
            3. Position sizing guidelines
            4. Stop loss and take profit levels
            5. Market conditions to avoid
            6. Expected performance metrics
            
            Make the strategy specific and actionable.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert quantitative trader with deep knowledge of financial markets and trading strategies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating strategy: {str(e)}"
    
    async def analyze_results(self, results: BacktestResult) -> str:
        """Analyze backtest results using OpenAI GPT"""
        try:
            metrics_summary = json.dumps(results.metrics, indent=2)
            
            prompt = f"""
            Analyze the following backtest results:
            
            Strategy: {results.request.strategy.strategy_name}
            Market: {results.request.market_type}
            
            Performance Metrics:
            {metrics_summary}
            
            Total Trades: {len(results.trades)}
            
            Please provide a comprehensive analysis including:
            1. Overall performance assessment
            2. Risk-adjusted returns evaluation
            3. Drawdown analysis
            4. Trade efficiency metrics
            5. Strengths and weaknesses of the strategy
            6. Recommendations for improvement
            7. Market conditions where this strategy performs best/worst
            
            Be specific and actionable in your recommendations.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert quantitative analyst specializing in backtesting and strategy performance evaluation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing results: {str(e)}"
    
    def _prepare_market_summary(self, market_data: MarketData) -> str:
        """Prepare market data summary for LLM"""
        if not market_data.data:
            return "No data available"
        
        first_price = market_data.data[0]
        last_price = market_data.data[-1]
        
        # Calculate basic statistics
        prices = [p.close for p in market_data.data]
        volumes = [p.volume for p in market_data.data]
        
        high_price = max(p.high for p in market_data.data)
        low_price = min(p.low for p in market_data.data)
        avg_price = sum(prices) / len(prices)
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        return f"""
        Time Period: {first_price.timestamp} to {last_price.timestamp}
        Data Points: {len(market_data.data)}
        Price Range: ${low_price:.2f} - ${high_price:.2f}
        Average Price: ${avg_price:.2f}
        Opening Price: ${first_price.open:.2f}
        Closing Price: ${last_price.close:.2f}
        Price Change: {((last_price.close - first_price.open) / first_price.open * 100):.2f}%
        Average Volume: {avg_volume:.0f}
        """


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not genai:
            raise ImportError("Google Generative AI package not installed")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    async def generate_analysis(self, market_data: MarketData, context: str) -> str:
        """Generate analysis using Google Gemini"""
        try:
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Analyze the following {market_data.market_type} market data for {market_data.symbol}:
            
            {data_summary}
            
            Context: {context}
            
            Provide comprehensive market analysis with trends, patterns, and trading insights.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.model.generate_content, prompt
            )
            
            return response.text
            
        except Exception as e:
            return f"Error generating analysis: {str(e)}"
    
    async def generate_strategy(self, market_data: MarketData, requirements: str) -> str:
        """Generate trading strategy using Google Gemini"""
        try:
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Create a trading strategy based on:
            
            Market Data: {data_summary}
            Requirements: {requirements}
            
            Include entry/exit rules, risk management, and performance expectations.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.model.generate_content, prompt
            )
            
            return response.text
            
        except Exception as e:
            return f"Error generating strategy: {str(e)}"
    
    async def analyze_results(self, results: BacktestResult) -> str:
        """Analyze backtest results using Google Gemini"""
        try:
            metrics_summary = json.dumps(results.metrics, indent=2)
            
            prompt = f"""
            Analyze these backtest results:
            
            Strategy: {results.request.strategy.strategy_name}
            Metrics: {metrics_summary}
            
            Provide performance assessment and improvement recommendations.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.model.generate_content, prompt
            )
            
            return response.text
            
        except Exception as e:
            return f"Error analyzing results: {str(e)}"
    
    def _prepare_market_summary(self, market_data: MarketData) -> str:
        """Prepare market data summary for LLM"""
        if not market_data.data:
            return "No data available"
        
        first_price = market_data.data[0]
        last_price = market_data.data[-1]
        
        return f"""
        Symbol: {market_data.symbol}
        Market: {market_data.market_type}
        Period: {first_price.timestamp} to {last_price.timestamp}
        Data Points: {len(market_data.data)}
        Price Change: {((last_price.close - first_price.open) / first_price.open * 100):.2f}%
        """


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not anthropic:
            raise ImportError("Anthropic package not installed")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    async def generate_analysis(self, market_data: MarketData, context: str) -> str:
        """Generate analysis using Anthropic Claude"""
        try:
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Analyze this {market_data.market_type} market data for {market_data.symbol}:
            
            {data_summary}
            
            Context: {context}
            
            Provide detailed market analysis including trends, patterns, and trading opportunities.
            """
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Error generating analysis: {str(e)}"
    
    async def generate_strategy(self, market_data: MarketData, requirements: str) -> str:
        """Generate trading strategy using Anthropic Claude"""
        try:
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Create a trading strategy based on:
            
            Market Data: {data_summary}
            Requirements: {requirements}
            
            Include specific entry/exit rules, risk management, and expected performance.
            """
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Error generating strategy: {str(e)}"
    
    async def analyze_results(self, results: BacktestResult) -> str:
        """Analyze backtest results using Anthropic Claude"""
        try:
            metrics_summary = json.dumps(results.metrics, indent=2)
            
            prompt = f"""
            Analyze these backtest results:
            
            Strategy: {results.request.strategy.strategy_name}
            Performance Metrics: {metrics_summary}
            
            Provide comprehensive performance analysis and improvement recommendations.
            """
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Error analyzing results: {str(e)}"
    
    def _prepare_market_summary(self, market_data: MarketData) -> str:
        """Prepare market data summary for LLM"""
        if not market_data.data:
            return "No data available"
        
        first_price = market_data.data[0]
        last_price = market_data.data[-1]
        
        return f"""
        Symbol: {market_data.symbol}
        Market: {market_data.market_type}
        Period: {first_price.timestamp} to {last_price.timestamp}
        Data Points: {len(market_data.data)}
        Price Change: {((last_price.close - first_price.open) / first_price.open * 100):.2f}%
        """


class LLMManager:
    """Manager for multiple LLM providers"""
    
    def __init__(self):
        self.providers = {}
    
    def add_provider(self, config: LLMConfig) -> None:
        """Add an LLM provider"""
        if config.provider == LLMProvider.OPENAI:
            self.providers[config.provider] = OpenAIProvider(config)
        elif config.provider == LLMProvider.GEMINI:
            self.providers[config.provider] = GeminiProvider(config)
        elif config.provider == LLMProvider.CLAUDE:
            self.providers[config.provider] = ClaudeProvider(config)
        else:
            # For other providers (Cloudflare, Qwen, DeepSeek), we'll use a generic HTTP provider
            self.providers[config.provider] = HTTPProvider(config)
    
    def get_provider(self, provider_name: LLMProvider) -> BaseLLMProvider:
        """Get a specific LLM provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not configured")
        return self.providers[provider_name]
    
    async def generate_analysis(self, provider_name: LLMProvider, market_data: MarketData, context: str) -> str:
        """Generate analysis using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.generate_analysis(market_data, context)
    
    async def generate_strategy(self, provider_name: LLMProvider, market_data: MarketData, requirements: str) -> str:
        """Generate strategy using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.generate_strategy(market_data, requirements)
    
    async def analyze_results(self, provider_name: LLMProvider, results: BacktestResult) -> str:
        """Analyze results using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.analyze_results(results)


class HTTPProvider(BaseLLMProvider):
    """Generic HTTP provider for API-based LLMs"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.endpoints = {
            LLMProvider.CLOUDFLARE: "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}",
            LLMProvider.QWEN: "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions"
        }
    
    async def generate_analysis(self, market_data: MarketData, context: str) -> str:
        """Generate analysis using HTTP API"""
        try:
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Analyze this {market_data.market_type} market data for {market_data.symbol}:
            
            {data_summary}
            
            Context: {context}
            
            Provide comprehensive market analysis.
            """
            
            return await self._make_request(prompt)
            
        except Exception as e:
            return f"Error generating analysis: {str(e)}"
    
    async def generate_strategy(self, market_data: MarketData, requirements: str) -> str:
        """Generate trading strategy using HTTP API"""
        try:
            data_summary = self._prepare_market_summary(market_data)
            
            prompt = f"""
            Create a trading strategy based on:
            
            Market Data: {data_summary}
            Requirements: {requirements}
            
            Include entry/exit rules and risk management.
            """
            
            return await self._make_request(prompt)
            
        except Exception as e:
            return f"Error generating strategy: {str(e)}"
    
    async def analyze_results(self, results: BacktestResult) -> str:
        """Analyze backtest results using HTTP API"""
        try:
            metrics_summary = json.dumps(results.metrics, indent=2)
            
            prompt = f"""
            Analyze these backtest results:
            
            Strategy: {results.request.strategy.strategy_name}
            Metrics: {metrics_summary}
            
            Provide performance analysis and recommendations.
            """
            
            return await self._make_request(prompt)
            
        except Exception as e:
            return f"Error analyzing results: {str(e)}"
    
    async def _make_request(self, prompt: str) -> str:
        """Make HTTP request to LLM API"""
        # This is a simplified implementation
        # Each provider would need specific request formatting
        return f"Response from {self.config.provider}: Analysis based on prompt"
    
    def _prepare_market_summary(self, market_data: MarketData) -> str:
        """Prepare market data summary for LLM"""
        if not market_data.data:
            return "No data available"
        
        first_price = market_data.data[0]
        last_price = market_data.data[-1]
        
        return f"""
        Symbol: {market_data.symbol}
        Market: {market_data.market_type}
        Period: {first_price.timestamp} to {last_price.timestamp}
        Data Points: {len(market_data.data)}
        Price Change: {((last_price.close - first_price.open) / first_price.open * 100):.2f}%
        """