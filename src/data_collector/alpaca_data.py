"""
数据采集器 - Alpaca 账户和持仓数据
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAccountRequest, GetPositionsRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AlpacaDataCollector:
    """Alpaca 账户和持仓数据采集器"""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        初始化
        
        Args:
            api_key: Alpaca API Key
            secret_key: Alpaca Secret Key
            paper: 是否使用模拟盘 (True = Paper Trading)
        """
        self.trading_client = TradingClient(api_key, secret_key, paper=paper)
        
        # Historical data client for quotes
        self.historical_client = StockHistoricalDataClient(api_key, secret_key)
    
    def get_account(self) -> Dict[str, Any]:
        """
        获取账户信息
        """
        try:
            account = self.trading_client.get_account()
            return {
                "id": account.id,
                "account_number": account.account_number,
                "status": account.status,
                "currency": account.currency,
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
                "buying_power": float(account.buying_power),
                "daytrading_buying_power": float(account.daytrading_buying_power),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "multiplier": float(account.multiplier),
                "pattern_day_trader": account.pattern_day_trader,
                "trading_mode": account.trading_mode,
            }
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return {}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        """
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "avg_entry_price": float(p.avg_entry_price),
                    "side": p.side,
                    "market_value": float(p.market_value),
                    "cost_basis": float(p.cost_basis),
                    "unrealized_pl": float(p.unrealized_pl),
                    "unrealized_plpc": float(p.unrealized_plpc),
                    "current_price": float(p.current_price),
                    "change_today": float(p.change_today),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取特定股票的持仓
        """
        try:
            position = self.trading_client.get_position(symbol)
            return {
                "symbol": position.symbol,
                "qty": float(position.qty),
                "avg_entry_price": float(position.avg_entry_price),
                "side": position.side,
                "market_value": float(position.market_value),
                "cost_basis": float(position.cost_basis),
                "unrealized_pl": float(position.unrealized_pl),
                "unrealized_plpc": float(position.unrealized_plpc),
                "current_price": float(position.current_price),
                "change_today": float(position.change_today),
            }
        except Exception as e:
            # 没有持仓会抛异常，这是正常的
            return None
    
    def get_orders(self, status: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取订单列表
        
        Args:
            status: open, closed, all
            limit: 返回数量限制
        """
        try:
            orders = self.trading_client.get_orders(status=status, limit=limit)
            return [
                {
                    "id": o.id,
                    "symbol": o.symbol,
                    "side": o.side,
                    "type": o.type,
                    "qty": float(o.qty) if o.qty else None,
                    "filled_qty": float(o.filled_qty) if o.filled_qty else 0,
                    "limit_price": float(o.limit_price) if o.limit_price else None,
                    "stop_price": float(o.stop_price) if o.stop_price else None,
                    "status": o.status,
                    "created_at": str(o.created_at),
                    "filled_at": str(o.filled_at) if o.filled_at else None,
                }
                for o in orders
            ]
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return []
    
    def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新报价
        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.historical_client.get_stock_latest_quote(request)
            
            quote = quotes[symbol]
            return {
                "symbol": symbol,
                "bid_price": quote.bid_price,
                "bid_size": quote.bid_size,
                "ask_price": quote.ask_price,
                "ask_size": quote.ask_size,
                "last_price": quote.last_price,
                "timestamp": str(quote.timestamp),
            }
        except Exception as e:
            logger.error(f"获取 {symbol} 报价失败: {e}")
            return None
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        获取账户摘要 (简化版)
        """
        account = self.get_account()
        positions = self.get_positions()
        
        total_unrealized_pl = sum(p["unrealized_pl"] for p in positions)
        
        return {
            "cash": account.get("cash", 0),
            "buying_power": account.get("buying_power", 0),
            "portfolio_value": account.get("portfolio_value", 0),
            "equity": account.get("equity", 0),
            "total_unrealized_pl": total_unrealized_pl,
            "positions_count": len(positions),
            "positions": {
                p["symbol"]: {
                    "qty": p["qty"],
                    "avg_entry_price": p["avg_entry_price"],
                    "current_price": p["current_price"],
                    "unrealized_pl": p["unrealized_pl"],
                    "unrealized_plpc": p["unrealized_plpc"],
                }
                for p in positions
            },
        }


# 便捷函数
def get_alpaca_account(api_key: str, secret_key: str, paper: bool = True) -> Dict[str, Any]:
    """快速获取账户摘要"""
    collector = AlpacaDataCollector(api_key, secret_key, paper)
    return collector.get_account_summary()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if api_key and secret_key:
        collector = AlpacaDataCollector(api_key, secret_key, paper=True)
        summary = collector.get_account_summary()
        print(f"账户摘要: {summary}")
    else:
        print("请配置 ALPACA_API_KEY 和 ALPACA_SECRET_KEY")
