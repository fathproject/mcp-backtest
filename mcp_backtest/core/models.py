"""
Core data models for MCP Backtest
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


class MarketType(str, Enum):
    """Supported market types"""
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"


class DataFormat(str, Enum):
    """Supported data formats"""
    CSV = "csv"
    JSON = "json"
    API = "api"


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    CLOUDFLARE = "cloudflare"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"


class PriceData(BaseModel):
    """Price data point"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketData(BaseModel):
    """Market data container"""
    symbol: str
    market_type: MarketType
    data: List[PriceData]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataSourceConfig(BaseModel):
    """Configuration for data sources"""
    source_type: DataFormat
    source_path: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_headers: Dict[str, str] = Field(default_factory=dict)
    api_params: Dict[str, Any] = Field(default_factory=dict)


class BacktestConfig(BaseModel):
    """Configuration for backtesting"""
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.001
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    benchmark: Optional[str] = None


class StrategyConfig(BaseModel):
    """Configuration for trading strategies"""
    strategy_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_management: Dict[str, Any] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    """Configuration for LLM integration"""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    custom_prompt: Optional[str] = None


class BacktestRequest(BaseModel):
    """Request model for backtesting"""
    data_source: DataSourceConfig
    market_type: MarketType
    strategy: StrategyConfig
    backtest_config: BacktestConfig
    llm_config: LLMConfig
    analysis_requirements: List[str] = Field(default_factory=list)


class TradeSignal(BaseModel):
    """Trading signal"""
    timestamp: datetime
    action: str  # 'buy', 'sell', 'hold'
    quantity: float
    price: float
    confidence: float
    reasoning: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BacktestResult(BaseModel):
    """Result from backtesting"""
    test_id: str
    request: BacktestRequest
    trades: List[TradeSignal]
    metrics: Dict[str, float]
    analysis: str
    result_matrix: Dict[str, Any]
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PerformanceMetrics(BaseModel):
    """Performance metrics for backtesting"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float