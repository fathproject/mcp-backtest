"""
Configuration management for MCP Backtest
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .core.models import LLMProvider, MarketType, DataFormat


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = "sqlite:///backtest.db"
    echo: bool = False


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"


class APIConfig(BaseModel):
    """API configuration"""
    rate_limit: int = 100  # requests per minute
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [".csv", ".json"]


class LLMProviderConfig(BaseModel):
    """LLM provider configuration"""
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3-sonnet-20240229"
    
    cloudflare_api_key: Optional[str] = None
    cloudflare_account_id: Optional[str] = None
    cloudflare_model: str = "@cf/meta/llama-2-7b-chat-int8"
    
    qwen_api_key: Optional[str] = None
    qwen_model: str = "qwen-plus"
    
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"


class BacktestDefaults(BaseModel):
    """Default backtest configuration"""
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.001
    risk_free_rate: float = 0.02


class StrategyDefaults(BaseModel):
    """Default strategy parameters"""
    moving_average_crossover: Dict[str, Any] = {
        "short_window": 10,
        "long_window": 30
    }
    
    rsi: Dict[str, Any] = {
        "rsi_period": 14,
        "oversold_level": 30,
        "overbought_level": 70
    }
    
    mean_reversion: Dict[str, Any] = {
        "window": 20,
        "std_dev": 2
    }
    
    momentum: Dict[str, Any] = {
        "lookback_period": 10,
        "momentum_threshold": 0.02
    }


class Config(BaseModel):
    """Main configuration class"""
    
    # Basic settings
    app_name: str = "MCP Backtest"
    version: str = "0.1.0"
    environment: str = "development"
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    llm_providers: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    backtest_defaults: BacktestDefaults = Field(default_factory=BacktestDefaults)
    strategy_defaults: StrategyDefaults = Field(default_factory=StrategyDefaults)
    
    # Data paths
    data_dir: str = "data"
    results_dir: str = "results"
    logs_dir: str = "logs"
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from environment and files"""
        
        # Load environment variables
        load_dotenv()
        
        # Create base config
        config = cls()
        
        # Load API keys from environment
        config.llm_providers.openai_api_key = os.getenv("OPENAI_API_KEY")
        config.llm_providers.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        config.llm_providers.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        config.llm_providers.cloudflare_api_key = os.getenv("CLOUDFLARE_API_KEY")
        config.llm_providers.cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        config.llm_providers.qwen_api_key = os.getenv("QWEN_API_KEY")
        config.llm_providers.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        # Load other environment variables
        config.database.url = os.getenv("DATABASE_URL", config.database.url)
        config.server.host = os.getenv("SERVER_HOST", config.server.host)
        config.server.port = int(os.getenv("SERVER_PORT", str(config.server.port)))
        config.server.debug = os.getenv("DEBUG", "false").lower() == "true"
        config.server.log_level = os.getenv("LOG_LEVEL", config.server.log_level)
        
        # Create directories
        for dir_name in [config.data_dir, config.results_dir, config.logs_dir]:
            Path(dir_name).mkdir(exist_ok=True)
        
        return config
    
    def get_llm_config(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get LLM configuration for a provider"""
        configs = {
            LLMProvider.OPENAI: {
                "api_key": self.llm_providers.openai_api_key,
                "model": self.llm_providers.openai_model
            },
            LLMProvider.GEMINI: {
                "api_key": self.llm_providers.gemini_api_key,
                "model": self.llm_providers.gemini_model
            },
            LLMProvider.CLAUDE: {
                "api_key": self.llm_providers.claude_api_key,
                "model": self.llm_providers.claude_model
            },
            LLMProvider.CLOUDFLARE: {
                "api_key": self.llm_providers.cloudflare_api_key,
                "account_id": self.llm_providers.cloudflare_account_id,
                "model": self.llm_providers.cloudflare_model
            },
            LLMProvider.QWEN: {
                "api_key": self.llm_providers.qwen_api_key,
                "model": self.llm_providers.qwen_model
            },
            LLMProvider.DEEPSEEK: {
                "api_key": self.llm_providers.deepseek_api_key,
                "model": self.llm_providers.deepseek_model
            }
        }
        
        return configs.get(provider, {})
    
    def get_strategy_defaults(self, strategy_name: str) -> Dict[str, Any]:
        """Get default parameters for a strategy"""
        return getattr(self.strategy_defaults, strategy_name, {})


# Global configuration instance
config = Config.load()


def get_config() -> Config:
    """Get the global configuration instance"""
    return config


def reload_config() -> Config:
    """Reload configuration"""
    global config
    config = Config.load()
    return config