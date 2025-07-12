"""
MetaAPI client for live trading integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import json

from ..core.models import MarketType
from ..config import get_config

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types for MetaAPI"""
    BUY = "ORDER_TYPE_BUY"
    SELL = "ORDER_TYPE_SELL"
    BUY_LIMIT = "ORDER_TYPE_BUY_LIMIT"
    SELL_LIMIT = "ORDER_TYPE_SELL_LIMIT"
    BUY_STOP = "ORDER_TYPE_BUY_STOP"
    SELL_STOP = "ORDER_TYPE_SELL_STOP"


class OrderState(Enum):
    """Order states"""
    PENDING = "ORDER_STATE_PENDING"
    FILLED = "ORDER_STATE_FILLED"
    CANCELLED = "ORDER_STATE_CANCELLED"
    REJECTED = "ORDER_STATE_REJECTED"


class Position:
    """Trading position"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.symbol = data.get("symbol")
        self.type = data.get("type")
        self.volume = data.get("volume", 0.0)
        self.open_price = data.get("openPrice", 0.0)
        self.current_price = data.get("currentPrice", 0.0)
        self.profit = data.get("profit", 0.0)
        self.open_time = data.get("openTime")
        self.comment = data.get("comment", "")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "type": self.type,
            "volume": self.volume,
            "open_price": self.open_price,
            "current_price": self.current_price,
            "profit": self.profit,
            "open_time": self.open_time,
            "comment": self.comment
        }


class MetaAPIClient:
    """MetaAPI client for live trading"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.metaapi.api_key
        self.account_id = self.config.metaapi.account_id
        self.region = self.config.metaapi.region
        self.platform = self.config.metaapi.platform
        
        self.base_url = f"https://mt-client-api-v1.{self.region}.agiliumtrade.agiliumtrade.ai"
        self.session: Optional[aiohttp.ClientSession] = None
        
        self.headers = {
            "auth-token": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request"""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method, url, headers=self.headers, json=data
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"MetaAPI request failed: {e}")
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return await self._request("GET", f"/users/current/accounts/{self.account_id}/account-information")
    
    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        response = await self._request("GET", f"/users/current/accounts/{self.account_id}/positions")
        return [Position(pos) for pos in response.get("positions", [])]
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get pending orders"""
        response = await self._request("GET", f"/users/current/accounts/{self.account_id}/orders")
        return response.get("orders", [])
    
    async def get_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        response = await self._request("GET", f"/users/current/accounts/{self.account_id}/symbols/{symbol}/current-price")
        return response
    
    async def place_order(self, symbol: str, order_type: OrderType, volume: float, 
                         price: Optional[float] = None, stop_loss: Optional[float] = None,
                         take_profit: Optional[float] = None, comment: str = "") -> Dict[str, Any]:
        """Place a trading order"""
        
        order_data = {
            "actionType": "ORDER_TYPE_BUY" if "BUY" in order_type.value else "ORDER_TYPE_SELL",
            "symbol": symbol,
            "volume": volume,
            "type": order_type.value,
            "comment": comment
        }
        
        if price is not None:
            order_data["openPrice"] = price
        
        if stop_loss is not None:
            order_data["stopLoss"] = stop_loss
        
        if take_profit is not None:
            order_data["takeProfit"] = take_profit
        
        return await self._request("POST", f"/users/current/accounts/{self.account_id}/trade", order_data)
    
    async def close_position(self, position_id: str) -> Dict[str, Any]:
        """Close a position"""
        return await self._request("POST", f"/users/current/accounts/{self.account_id}/positions/{position_id}/close")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a pending order"""
        return await self._request("DELETE", f"/users/current/accounts/{self.account_id}/orders/{order_id}")
    
    async def get_history(self, symbol: str, timeframe: str = "1h", 
                         start_time: Optional[datetime] = None, 
                         end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get historical price data"""
        
        params = {
            "symbol": symbol,
            "timeframe": timeframe
        }
        
        if start_time:
            params["startTime"] = start_time.isoformat()
        
        if end_time:
            params["endTime"] = end_time.isoformat()
        
        response = await self._request("GET", f"/users/current/accounts/{self.account_id}/historical-market-data", params)
        return response.get("candles", [])
    
    async def get_account_equity(self) -> float:
        """Get account equity"""
        account_info = await self.get_account_info()
        return account_info.get("equity", 0.0)
    
    async def get_account_balance(self) -> float:
        """Get account balance"""
        account_info = await self.get_account_info()
        return account_info.get("balance", 0.0)
    
    async def get_account_margin(self) -> float:
        """Get used margin"""
        account_info = await self.get_account_info()
        return account_info.get("margin", 0.0)
    
    async def get_free_margin(self) -> float:
        """Get free margin"""
        account_info = await self.get_account_info()
        return account_info.get("freeMargin", 0.0)
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is available for trading"""
        try:
            await self.get_price(symbol)
            return True
        except:
            return False
    
    async def calculate_position_size(self, symbol: str, risk_percent: float, 
                                    stop_loss_pips: float) -> float:
        """Calculate position size based on risk management"""
        try:
            account_info = await self.get_account_info()
            equity = account_info.get("equity", 0.0)
            
            # Calculate risk amount
            risk_amount = equity * (risk_percent / 100)
            
            # Get symbol info for pip value calculation
            # This is a simplified calculation - in reality you'd need symbol specifications
            pip_value = 1.0  # Default pip value
            
            # Calculate position size
            position_size = risk_amount / (stop_loss_pips * pip_value)
            
            return min(position_size, equity * 0.1)  # Max 10% of equity
        
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01  # Minimum position size