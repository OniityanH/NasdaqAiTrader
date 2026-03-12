"""
数据采集器 - 使用 yfinance 获取股票数据
Yahoo Finance 免费数据，无需 API Key
"""
import yfinance as yf
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class YFinanceCollector:
    """yfinance 数据采集器"""
    
    def __init__(self):
        pass
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取实时报价
        
        Returns:
            包含价格数据的字典 (兼容 FMP 格式)
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                logger.warning(f"无法获取 {symbol} 的数据")
                return None
            
            return {
                "symbol": symbol,
                "price": info.get("currentPrice"),
                "open": info.get("open"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "volume": info.get("volume"),
                "marketCap": info.get("marketCap"),  # 使用 camelCase 兼容 FMP
                "change": info.get("regularMarketChange"),
                "changes_percentage": info.get("regularMarketChangePercent"),
                "year_high": info.get("fiftyTwoWeekHigh"),  # 52周高低
                "year_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
            }
            
        except Exception as e:
            logger.error(f"获取 {symbol} 报价失败: {e}")
            return None
    
    def get_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取公司基本信息
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return {
                "symbol": symbol,
                "company_name": info.get("shortName"),  # 公司名称
                "exchange": info.get("exchange"),
                "currency": info.get("currency"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "ipoDate": info.get("ipoDate"),  # IPO日期
                "beta": info.get("beta"),
                "vol_avg": info.get("averageVolume"),
                "priceAvg50": info.get("fiftyDayAverage"),
                "priceAvg200": info.get("twoHundredDayAverage"),
            }
            
        except Exception as e:
            logger.error(f"获取 {symbol} 基本信息失败: {e}")
            return None
    
    def get_key_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取关键财务指标
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return {
                "symbol": symbol,
                "peRatio": info.get("trailingPE"),  # 市盈率
                "pegRatio": info.get("pegRatio"),
                "eps": info.get("trailingEps"),  # 每股收益
                "currentRatio": info.get("currentRatio"),
                "quickRatio": info.get("quickRatio"),
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "debtEquity": info.get("debtToEquity"),
            }
            
        except Exception as e:
            logger.error(f"获取 {symbol} 关键指标失败: {e}")
            return None
    
    def get_price_target(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取分析师目标价
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return {
                "symbol": symbol,
                "price_target_avg": info.get("targetMeanPrice"),
                "price_target_high": info.get("targetHighPrice"),
                "price_target_low": info.get("targetLowPrice"),
                "rating": info.get("recommendationKey"),  # 评级
                "total_analysts": info.get("numberOfAnalystOpinions"),  # 分析师数量
            }
            
        except Exception as e:
            logger.error(f"获取 {symbol} 目标价失败: {e}")
            return None
    
    def get_price_history(self, symbol: str, period: str = "1mo") -> List[Dict[str, Any]]:
        """
        获取历史价格
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return []
            
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                })
            
            return records
            
        except Exception as e:
            logger.error(f"获取 {symbol} 历史价格失败: {e}")
            return []
    
    def get_all_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取该股票的所有数据 (兼容 FMP 格式)
        """
        result = {
            "symbol": symbol,
        }
        
        # 基本信息
        profile = self.get_profile(symbol)
        if profile:
            result["profile"] = profile
        
        # 报价
        quote = self.get_quote(symbol)
        if quote:
            result["quote"] = quote
            # 把一些常用指标直接放到quote层级，方便访问
            metrics = self.get_key_metrics(symbol)
            if metrics:
                result["metrics"] = metrics
                # 将PE、EPS放到quote中，简化访问
                quote["pe"] = metrics.get("peRatio")
                quote["eps"] = metrics.get("eps")
        
        # 目标价
        price_target = self.get_price_target(symbol)
        if price_target:
            result["price_target"] = price_target
        
        return result


# 便捷函数
def get_stock_data(symbol: str) -> Dict[str, Any]:
    """快速获取股票数据"""
    collector = YFinanceCollector()
    return collector.get_all_data(symbol)


if __name__ == "__main__":
    collector = YFinanceCollector()
    data = collector.get_all_data("AAPL")
    print(f"AAPL 数据: {data}")
