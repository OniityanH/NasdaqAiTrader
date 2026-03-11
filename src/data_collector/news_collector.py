"""
数据采集器 - 新闻数据
使用 Finnhub 和 Alpha Vantage 获取新闻
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NewsCollector:
    """新闻数据采集器"""
    
    def __init__(self, finnhub_key: str = None, alpha_vantage_key: str = None):
        """
        初始化
        
        Args:
            finnhub_key: Finnhub API Key
            alpha_vantage_key: Alpha Vantage API Key
        """
        self.finnhub_key = finnhub_key
        self.alpha_vantage_key = alpha_vantage_key
        self.finnhub_base = "https://finnhub.io/api/v1"
    
    def get_finnhub_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取 Finnhub 新闻
        
        Args:
            symbol: 股票代码
            limit: 返回数量
            
        Returns:
            新闻列表
        """
        if not self.finnhub_key or self.finnhub_key == "YOUR_FINNHUB_KEY":
            logger.warning("Finnhub API Key 未配置")
            return []
        
        # 计算日期范围 (最近7天)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=7)
        
        params = {
            "symbol": symbol,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "token": self.finnhub_key
        }
        
        try:
            response = requests.get(
                f"{self.finnhub_base}/news",
                params=params,
                timeout=10
            )
            data = response.json()
            
            if isinstance(data, list):
                return [
                    {
                        "id": item.get("id"),
                        "datetime": item.get("datetime"),
                        "headline": item.get("headline"),
                        "summary": item.get("summary"),
                        "source": item.get("source"),
                        "url": item.get("url"),
                        "image": item.get("image"),
                        "category": item.get("category"),
                        "related": item.get("related"),
                    }
                    for item in data[:limit]
                ]
            return []
            
        except Exception as e:
            logger.error(f"获取 Finnhub 新闻失败: {e}")
            return []
    
    def get_finnhub_general_news(self, category: str = "general", limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取市场新闻
        """
        if not self.finnhub_key or self.finnhub_key == "YOUR_FINNHUB_KEY":
            return []
        
        params = {
            "category": category,
            "token": self.finnhub_key
        }
        
        try:
            response = requests.get(
                f"{self.finnhub_base}/news",
                params=params,
                timeout=10
            )
            data = response.json()
            
            if isinstance(data, list):
                return [
                    {
                        "headline": item.get("headline"),
                        "summary": item.get("summary"),
                        "source": item.get("source"),
                        "url": item.get("url"),
                        "image": item.get("image"),
                        "datetime": item.get("datetime"),
                    }
                    for item in data[:limit]
                ]
            return []
            
        except Exception as e:
            logger.error(f"获取通用新闻失败: {e}")
            return []
    
    def get_alpha_vantage_news(self, symbols: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取 Alpha Vantage 新闻
        
        Args:
            symbols: 股票代码列表
            limit: 返回数量
        """
        if not self.alpha_vantage_key or self.alpha_vantage_key == "YOUR_ALPHA_VANTAGE_KEY":
            logger.warning("Alpha Vantage API Key 未配置")
            return []
        
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ",".join(symbols) if symbols else "",
            "limit": limit,
            "apikey": self.alpha_vantage_key
        }
        
        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params=params,
                timeout=10
            )
            data = response.json()
            
            feed = data.get("feed", [])
            return [
                {
                    "title": item.get("title"),
                    "summary": item.get("summary"),
                    "source": item.get("source"),
                    "url": item.get("url"),
                    "banner_image": item.get("banner_image"),
                    "time_published": item.get("time_published"),
                    "overall_sentiment_score": item.get("overall_sentiment_score"),
                    "overall_sentiment_label": item.get("overall_sentiment_label"),
                    "ticker_sentiment": item.get("ticker_sentiment", []),
                }
                for item in feed[:limit]
            ]
            
        except Exception as e:
            logger.error(f"获取 Alpha Vantage 新闻失败: {e}")
            return []
    
    def get_news_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取新闻情绪分析 (Finnhub)
        """
        if not self.finnhub_key or self.finnhub_key == "YOUR_FINNHUB_KEY":
            return None
        
        params = {
            "symbol": symbol,
            "token": self.finnhub_key
        }
        
        try:
            response = requests.get(
                f"{self.finnhub_base}/news-sentiment",
                params=params,
                timeout=10
            )
            data = response.json()
            
            if data.get("symbol"):
                return {
                    "symbol": data.get("symbol"),
                    "buzz": data.get("buzz"),
                    "company_news_score": data.get("companyNewsScore"),
                    "sector_average_bullish_percent": data.get("sectorAverageBullishPercent"),
                    "sector_average_news_score": data.get("sectorAverageNewsScore"),
                    "sentiment": data.get("sentiment"),
                    "bearish_percent": data.get("sentiment", {}).get("bearishPercent", 0),
                    "bullish_percent": data.get("sentiment", {}).get("bullishPercent", 0),
                }
            return None
            
        except Exception as e:
            logger.error(f"获取新闻情绪失败: {e}")
            return None
    
    def get_all_news(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """
        获取所有来源的新闻
        
        Returns:
            整合后的新闻数据
        """
        result = {
            "symbol": symbol,
            "finnhub": [],
            "alpha_vantage": [],
            "sentiment": None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Finnhub 新闻
        finnhub_news = self.get_finnhub_news(symbol, limit)
        if finnhub_news:
            result["finnhub"] = finnhub_news
        
        # Alpha Vantage 新闻
        av_news = self.get_alpha_vantage_news([symbol], limit)
        if av_news:
            result["alpha_vantage"] = av_news
        
        # 新闻情绪
        sentiment = self.get_news_sentiment(symbol)
        if sentiment:
            result["sentiment"] = sentiment
        
        return result
    
    def format_for_ai(self, news_data: Dict[str, Any]) -> str:
        """
        格式化新闻为 AI 决策可用的格式
        """
        all_news = []
        
        # 添加 Finnhub 新闻
        for item in news_data.get("finnhub", [])[:3]:
            all_news.append({
                "title": item.get("headline", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "datetime": item.get("datetime"),
            })
        
        # 添加 Alpha Vantage 新闻
        for item in news_data.get("alpha_vantage", [])[:3]:
            all_news.append({
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "sentiment": item.get("overall_sentiment_label", "neutral"),
                "time": item.get("time_published", ""),
            })
        
        # 格式化输出
        if not all_news:
            return "无新闻"
        
        lines = []
        for i, news in enumerate(all_news[:5], 1):
            sentiment_emoji = ""
            if news.get("sentiment"):
                sent = news["sentiment"].lower()
                if "bullish" in sent:
                    sentiment_emoji = "📈 "
                elif "bearish" in sent:
                    sentiment_emoji = "📉 "
            
            lines.append(f"{i}. {sentiment_emoji}{news.get('title', '')[:100]}")
        
        return "\n".join(lines)


# 便捷函数
def get_stock_news(
    symbol: str,
    finnhub_key: str = None,
    alpha_vantage_key: str = None
) -> Dict[str, Any]:
    """快速获取新闻"""
    collector = NewsCollector(finnhub_key, alpha_vantage_key)
    return collector.get_all_news(symbol)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 测试
    finnhub_key = os.getenv("FINNHUB_KEY", "")
    av_key = os.getenv("ALPHA_VANTAGE_KEY", "")
    
    if finnhub_key:
        collector = NewsCollector(finnhub_key, av_key)
        news = collector.get_all_news("AAPL")
        print(f"新闻: {news}")
    else:
        print("请配置 FINNHUB_KEY")
