"""
交易循环调度器
"""
import time
import logging
from datetime import datetime, time as dt_time
from typing import List, Dict, Any, Optional
import yaml
import os
from dotenv import load_dotenv

from ..data_bus.data_manager import DataBus, format_stock_data_for_ai
from ..ai_brain.deepseek_client import DeepSeekBrain
from ..trader.alpaca_trader import AlpacaTrader

logger = logging.getLogger(__name__)


class TradingScheduler:
    """交易循环调度器"""
    
    def __init__(
        self,
        config_path: str = "config/api_keys.yaml"
    ):
        """初始化"""
        # 加载配置
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # 提取配置
        api_config = self.config
        
        # 初始化数据总线
        self.data_bus = DataBus(
            alpha_vantage_key=api_config.get("ALPHA_VANTAGE_KEY", ""),
            fmp_key=api_config.get("FMP_KEY", ""),
            alpaca_api_key=api_config.get("ALPACA_API_KEY", ""),
            alpaca_secret_key=api_config.get("ALPACA_SECRET_KEY", ""),
            alpaca_paper=api_config.get("ALPACA_PAPER", True)
        )
        
        # 初始化 AI 大脑
        self.ai_brain = DeepSeekBrain(
            api_key=api_config.get("DEEPSEEK_API_KEY", ""),
            base_url=api_config.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        
        # 初始化交易执行器
        self.trader = AlpacaTrader(
            api_key=api_config.get("ALPACA_API_KEY", ""),
            secret_key=api_config.get("ALPACA_SECRET_KEY", ""),
            paper=api_config.get("ALPACA_PAPER", True)
        )
        
        # 交易配置
        trading_config = api_config.get("TRADING", {})
        self.watchlist = trading_config.get("WATCHLIST", [])
        self.interval = trading_config.get("INTERVAL", 300)
        self.risk_config = {
            "stop_loss": trading_config.get("STOP_LOSS", 0.05),
            "take_profit": trading_config.get("TAKE_PROFIT", 0.15),
            "max_position": trading_config.get("MAX_POSITION", 0.20),
            "max_trade": trading_config.get("MAX_TRADE", 0.10),
            "max_daily_loss": trading_config.get("MAX_DAILY_LOSS", 0.03),
            "risk_preference": trading_config.get("RISK_PREFERENCE", "conservative"),
        }
        
        # 状态
        self.running = False
        self.daily_pnl = 0.0
        self.last_trade_date = None
        
        logger.info(f"交易调度器初始化完成, 监控: {self.watchlist}")
    
    def is_trading_hours(self) -> bool:
        """检查是否在交易时间 (美股)"""
        now = datetime.now()
        
        # 美股交易时间: 9:30 - 16:00 EST
        # 简化: 这里不做严格检查，默认都运行
        # 实际生产应该检查
        
        # 周末不交易
        if now.weekday() >= 5:
            return False
        
        return True
    
    def check_risk_limits(self) -> bool:
        """
        检查风控限制
        
        Returns:
            True = 可以交易, False = 停止交易
        """
        # 检查单日亏损
        if self.daily_pnl <= -self.risk_config["max_daily_loss"]:
            logger.warning(f"触发日亏损限制: {self.daily_pnl:.2%}, 停止交易")
            return False
        
        return True
    
    def process_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        处理单只股票
        
        Returns:
            处理结果
        """
        result = {
            "symbol": symbol,
            "success": False,
            "decision": None,
            "trade": None,
            "error": None
        }
        
        try:
            # 1. 获取数据
            stock_data_raw = self.data_bus.get_stock_data(symbol)
            stock_data = format_stock_data_for_ai(stock_data_raw)
            
            # 2. AI 决策
            decision = self.ai_brain.make_decision(stock_data, self.risk_config)
            result["decision"] = decision
            
            # 3. 获取最新账户信息
            account = self.data_bus.get_account_summary()
            cash = account.get("cash", 0)
            
            # 4. 获取持仓
            position = stock_data_raw.get("position", {})
            position_qty = position.get("qty", 0) if position else 0
            current_price = stock_data.get("current_price", 0)
            
            # 5. 执行交易
            trade_result = self.trader.execute_trade(
                symbol=symbol,
                decision=decision,
                current_price=current_price,
                position_qty=position_qty,
                cash=cash,
                risk_config=self.risk_config
            )
            
            result["trade"] = trade_result
            result["success"] = True
            
            logger.info(f"{symbol} 处理完成: {decision.get('decision')} - {decision.get('reason')}")
            
        except Exception as e:
            logger.error(f"处理 {symbol} 失败: {e}")
            result["error"] = str(e)
        
        return result
    
    def run_once(self) -> List[Dict[str, Any]]:
        """
        运行一次交易循环
        """
        results = []
        
        # 检查风控
        if not self.check_risk_limits():
            logger.warning("风控限制触发，跳过本次交易")
            return results
        
        # 检查交易时间
        if not self.is_trading_hours():
            logger.info("非交易时间，跳过")
            return results
        
        logger.info(f"=== 开始交易循环 ({datetime.now().strftime('%H:%M:%S')}) ===")
        
        # 处理每只股票
        for symbol in self.watchlist:
            result = self.process_symbol(symbol)
            results.append(result)
            
            # 避免API限流
            time.sleep(2)
        
        logger.info(f"=== 交易循环完成 ===")
        
        return results
    
    def run(self, max_iterations: Optional[int] = None):
        """
        持续运行交易循环
        
        Args:
            max_iterations: 最大迭代次数，None 表示无限
        """
        self.running = True
        iteration = 0
        
        logger.info("开始交易机器人...")
        
        while self.running:
            iteration += 1
            
            try:
                self.run_once()
                
                # 检查是否停止
                if max_iterations and iteration >= max_iterations:
                    logger.info(f"达到最大迭代次数 {max_iterations}，停止")
                    break
                
                # 等待下一个周期
                logger.info(f"等待 {self.interval} 秒...")
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("收到停止信号")
                break
            except Exception as e:
                logger.error(f"交易循环异常: {e}")
                time.sleep(60)  # 异常后等待1分钟
        
        self.running = False
        logger.info("交易机器人已停止")
    
    def stop(self):
        """停止交易"""
        self.running = False


def load_config(config_path: str = "config/api_keys.yaml") -> Dict[str, Any]:
    """加载配置"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载环境变量
    load_dotenv()
    
    # 测试运行一次
    scheduler = TradingScheduler()
    results = scheduler.run_once()
    
    print(f"\n处理结果: {results}")
