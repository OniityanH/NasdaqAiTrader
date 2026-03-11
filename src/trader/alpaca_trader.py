"""
交易执行 - Alpaca
"""
import logging
from typing import Dict, Any, Optional, List
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

logger = logging.getLogger(__name__)


class AlpacaTrader:
    """Alpaca 交易执行器"""
    
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True
    ):
        """
        初始化
        
        Args:
            api_key: Alpaca API Key
            secret_key: Alpaca Secret Key
            paper: 是否使用模拟盘
        """
        self.client = TradingClient(api_key, secret_key, paper=paper)
        self.paper = paper
        
        if paper:
            logger.info("Alpaca 交易模式: Paper Trading (模拟盘)")
        else:
            logger.warning("Alpaca 交易模式: 实盘! 请注意风险!")
    
    def get_account(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            account = self.client.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "status": account.status,
            }
        except Exception as e:
            logger.error(f"获取账户失败: {e}")
            return {}
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓"""
        try:
            position = self.client.get_position(symbol)
            return {
                "symbol": position.symbol,
                "qty": float(position.qty),
                "avg_entry_price": float(position.avg_entry_price),
                "market_value": float(position.market_value),
                "unrealized_pl": float(position.unrealized_pl),
            }
        except Exception:
            return None
    
    def place_market_order(
        self,
        symbol: str,
        qty: int,
        side: str,  # "buy" or "sell"
        time_in_force: str = "day"
    ) -> Optional[Dict[str, Any]]:
        """
        市价单
        
        Args:
            symbol: 股票代码
            qty: 数量
            side: buy/sell
            time_in_force: day, gtc, ioc, fok
            
        Returns:
            订单信息
        """
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce(time_in_force)
        
        try:
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=tif
            )
            
            result = self.client.submit_order(order)
            
            logger.info(f"市价单提交成功: {side} {qty} {symbol}")
            
            return {
                "id": result.id,
                "symbol": result.symbol,
                "side": result.side,
                "type": result.type,
                "qty": float(result.qty),
                "filled_qty": float(result.filled_qty) if result.filled_qty else 0,
                "status": result.status,
                "submitted_at": str(result.submitted_at),
            }
            
        except Exception as e:
            logger.error(f"市价单下单失败: {e}")
            return {"error": str(e)}
    
    def place_limit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        limit_price: float,
        time_in_force: str = "day"
    ) -> Optional[Dict[str, Any]]:
        """
        限价单
        """
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce(time_in_force)
        
        try:
            order = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                limit_price=limit_price,
                time_in_force=tif
            )
            
            result = self.client.submit_order(order)
            
            logger.info(f"限价单提交成功: {side} {qty} {symbol} @ ${limit_price}")
            
            return {
                "id": result.id,
                "symbol": result.symbol,
                "side": result.side,
                "type": result.type,
                "qty": float(result.qty),
                "limit_price": float(result.limit_price) if result.limit_price else None,
                "status": result.status,
            }
            
        except Exception as e:
            logger.error(f"限价单下单失败: {e}")
            return {"error": str(e)}
    
    def place_stop_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        stop_price: float,
        time_in_force: str = "gtc"
    ) -> Optional[Dict[str, Any]]:
        """
        止损单
        """
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce(time_in_force)
        
        try:
            order = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                stop_price=stop_price,
                time_in_force=tif
            )
            
            result = self.client.submit_order(order)
            
            logger.info(f"止损单提交成功: {side} {qty} {symbol} @ ${stop_price}")
            
            return {
                "id": result.id,
                "symbol": result.symbol,
                "side": result.side,
                "type": result.type,
                "stop_price": float(result.stop_price) if result.stop_price else None,
                "status": result.status,
            }
            
        except Exception as e:
            logger.error(f"止损单下单失败: {e}")
            return {"error": str(e)}
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            self.client.cancel_order(order_id)
            logger.info(f"订单取消成功: {order_id}")
            return True
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态"""
        try:
            order = self.client.get_order(order_id)
            return {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "qty": float(order.qty),
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "status": order.status,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "stop_price": float(order.stop_price) if order.stop_price else None,
            }
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return None
    
    def execute_buy(
        self,
        symbol: str,
        current_price: float,
        cash: float,
        max_position_pct: float = 0.10,
        use_limit: bool = False,
        limit_offset: float = 0.001
    ) -> Optional[Dict[str, Any]]:
        """
        执行买入
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            cash: 可用资金
            max_position_pct: 最大仓位比例
            use_limit: 是否使用限价单
            limit_offset: 限价单偏移比例
            
        Returns:
            订单结果
        """
        # 计算买入数量 (使用10%仓位)
        max_amount = cash * max_position_pct
        qty = int(max_amount / current_price)
        
        if qty <= 0:
            logger.warning(f"资金不足，无法买入 {symbol}")
            return {"error": "insufficient_funds"}
        
        if use_limit:
            # 限价单 - 比市价低1%
            limit_price = current_price * (1 - limit_offset)
            return self.place_limit_order(symbol, qty, "buy", limit_price)
        else:
            return self.place_market_order(symbol, qty, "buy")
    
    def execute_sell(
        self,
        symbol: str,
        current_price: float,
        position_qty: int,
        set_stop_loss: float = None,
        use_limit: bool = False,
        limit_offset: float = 0.001
    ) -> Optional[Dict[str, Any]]:
        """
        执行卖出
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            position_qty: 持仓数量
            set_stop_loss: 设置止损价格
            use_limit: 是否使用限价单
            limit_offset: 限价单偏移比例
            
        Returns:
            订单结果
        """
        if position_qty <= 0:
            logger.warning(f"无持仓，无法卖出 {symbol}")
            return {"error": "no_position"}
        
        if use_limit:
            limit_price = current_price * (1 + limit_offset)
            order = self.place_limit_order(symbol, position_qty, "sell", limit_price)
        else:
            order = self.place_market_order(symbol, position_qty, "sell")
        
        # 如果需要设置止损 (用卖出后的资金买入看跌期权或其他)
        # 这里可以添加逻辑
        
        return order
    
    def execute_trade(
        self,
        symbol: str,
        decision: Dict[str, Any],
        current_price: float,
        position_qty: int,
        cash: float,
        risk_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行交易决策
        
        Args:
            symbol: 股票代码
            decision: AI 决策结果
            current_price: 当前价格
            position_qty: 当前持仓
            cash: 可用资金
            risk_config: 风控配置
            
        Returns:
            执行结果
        """
        decision_type = decision.get("decision", "HOLD")
        shares = decision.get("shares", 0)
        
        result = {
            "symbol": symbol,
            "decision": decision_type,
            "executed": False,
            "orders": []
        }
        
        # 检查是否需要止损
        if position_qty > 0:
            avg_price = 0  # TODO: 获取持仓成本
            if avg_price > 0:
                pnl_pct = (current_price - avg_price) / avg_price
                if pnl_pct <= -risk_config.get("stop_loss", 0.05):
                    logger.warning(f"触发止损: {symbol}, 亏损 {pnl_pct:.2%}")
                    # 强制卖出
                    order = self.execute_sell(symbol, current_price, position_qty)
                    result["executed"] = True
                    result["orders"].append(order)
                    result["reason"] = "强制止损"
                    return result
        
        # 根据决策执行
        if decision_type == "BUY" and shares > 0:
            # 买入
            order = self.execute_buy(
                symbol,
                current_price,
                cash,
                risk_config.get("max_trade", 0.10)
            )
            result["executed"] = True
            result["orders"].append(order)
            result["reason"] = decision.get("reason", "")
            
        elif decision_type == "SELL" and position_qty > 0:
            # 卖出
            sell_qty = min(shares, position_qty)
            order = self.execute_sell(symbol, current_price, sell_qty)
            result["executed"] = True
            result["orders"].append(order)
            result["reason"] = decision.get("reason", "")
        
        else:
            result["reason"] = " HOLD - 无需操作"
        
        return result


# 便捷函数
def execute_trade_order(
    api_key: str,
    secret_key: str,
    paper: bool,
    symbol: str,
    decision: Dict[str, Any],
    current_price: float,
    position_qty: int,
    cash: float,
    risk_config: Dict[str, Any]
) -> Dict[str, Any]:
    """快速执行交易"""
    trader = AlpacaTrader(api_key, secret_key, paper)
    return trader.execute_trade(symbol, decision, current_price, position_qty, cash, risk_config)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if api_key and secret_key:
        trader = AlpacaTrader(api_key, secret_key, paper=True)
        
        # 获取账户
        account = trader.get_account()
        print(f"账户: {account}")
    else:
        print("请配置 ALPACA_API_KEY 和 ALPACA_SECRET_KEY")
