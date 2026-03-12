"""
数据采集器 - 股票行情数据
使用 Alpha Vantage API 获取实时价格和历史数据
"""
import requests
import time
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """Alpha Vantage 市场数据采集器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self._rate_limit_delay = 12  # 免费版 5次/分钟，间隔12秒
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取实时报价
        
        Args:
            symbol: 股票代码，如 "AAPL"
            
        Returns:
            包含价格数据的字典
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            # 缩短超时时间，避免长时间等待
            response = requests.get(self.base_url, params=params, timeout=5)
            data = response.json()
            
            # 检查是否有速率限制错误
            if isinstance(data, dict) and "Information" in data:
                logger.warning(f"Alpha Vantage 速率限制: {data.get('Information')}")
                return None
            
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                return {
                    "symbol": quote.get("01. symbol"),
                    "current_price": float(quote.get("02. price", 0)),
                    "open": float(quote.get("03. open", 0)),
                    "high": float(quote.get("04. high", 0)),
                    "low": float(quote.get("05. low", 0)),
                    "volume": int(quote.get("06. volume", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_pct": float(quote.get("10. change %", "0").replace("%", "")),
                }
            else:
                logger.warning(f"无法获取 {symbol} 的报价: {data}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Alpha Vantage 请求超时: {symbol}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Alpha Vantage 请求错误: {symbol} - {e}")
            return None
        except Exception as e:
            logger.error(f"获取 {symbol} 报价失败: {e}")
            return None
    
    def get_intraday(self, symbol: str, interval: str = "5min") -> Optional[Dict]:
        """
        获取日内K线数据
        
        Args:
            symbol: 股票代码
            interval: 时间间隔 (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            K线数据字典
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": "compact",
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            time_series_key = f"Time Series ({interval})"
            if time_series_key in data:
                return data[time_series_key]
            else:
                logger.warning(f"无法获取 {symbol} 日内数据")
                return None
                
        except Exception as e:
            logger.error(f"获取 {symbol} 日内数据失败: {e}")
            return None
    
    def get_daily(self, symbol: str, outputsize: str = "compact") -> Optional[Dict]:
        """
        获取日K线数据
        
        Args:
            symbol: 股票代码
            outputsize: compact (100天) / full (全部历史)
            
        Returns:
            日K线数据
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if "Time Series (Daily)" in data:
                return data["Time Series (Daily)"]
            else:
                logger.warning(f"无法获取 {symbol} 日K数据")
                return None
                
        except Exception as e:
            logger.error(f"获取 {symbol} 日K数据失败: {e}")
            return None
    
    def get_technical_indicators(self, symbol: str, indicator: str = "SMA", 
                                 time_period: int = 50) -> Optional[Dict]:
        """
        获取技术指标
        
        Args:
            symbol: 股票代码
            indicator: 指标类型 (SMA, EMA, RSI, MACD)
            time_period: 周期
            
        Returns:
            技术指标数据
        """
        # Alpha Vantage 技术指标函数映射
        indicator_map = {
            "SMA": "SMA",
            "EMA": "EMA",
            "RSI": "RSI",
            "MACD": "MACD",
            "BB": "BBANDS"
        }
        
        func = indicator_map.get(indicator, "SMA")
        
        params = {
            "function": func,
            "symbol": symbol,
            "interval": "daily",
            "time_period": time_period,
            "series_type": "close",
            "apikey": self.api_key
        }
        
        # MACD 特殊处理
        if indicator == "MACD":
            params.pop("time_period", None)
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            key = f"Technical Analysis: {func}"
            if key in data:
                return data[key]
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取 {symbol} 技术指标失败: {e}")
            return None
    
    def rate_limit_wait(self):
        """遵守 API 频率限制"""
        time.sleep(self._rate_limit_delay)


# 便捷函数
def get_market_data(symbol: str, alpha_vantage_key: str) -> Optional[Dict]:
    """快速获取市场数据"""
    collector = MarketDataCollector(alpha_vantage_key)
    quote = collector.get_quote(symbol)
    collector.rate_limit_wait()
    return quote


if __name__ == "__main__":
    # 测试
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("ALPHA_VANTAGE_KEY", "demo")
    
    collector = MarketDataCollector(api_key)
    data = collector.get_quote("AAPL")
    print(f"AAPL 当前价格: ${data}")
