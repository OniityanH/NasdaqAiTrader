"""
数据采集器 - 新闻数据
使用 NewsData.io API 获取美股新闻
"""
import requests
from typing import Optional, Dict, Any, List
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsDataCollector:
    """NewsData.io 新闻采集器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsdata.io/api/1/latest"
        self._rate_limit_delay = 2  # 免费版 200次/天，间隔2秒足够
    
    def _is_today(self, pub_date: str) -> bool:
        """检查新闻日期是否是今天"""
        if not pub_date:
            return False
        try:
            # 解析新闻日期 (格式: 2026-03-12 14:28:40)
            news_date = datetime.strptime(pub_date.split('.')[0], "%Y-%m-%d %H:%M:%S")
            today = datetime.now()
            return news_date.date() == today.date()
        except:
            return False
    
    def get_stock_news(self, symbols: List[str], limit: int = 30) -> List[Dict[str, Any]]:
        """
        获取股票相关新闻 (默认获取30条，筛选当天新闻)
        
        Args:
            symbols: 股票代码列表
            limit: 返回新闻数量 (默认30)
            
        Returns:
            新闻列表 (只返回当天新闻)
        """
        all_news = []
        
        for symbol in symbols:
            news = self._get_news_for_symbol(symbol, limit)
            if news:
                all_news.extend(news)
            time.sleep(self._rate_limit_delay)
        
        # 筛选当天的新闻
        today_news = [n for n in all_news if self._is_today(n.get('pubDate', ''))]
        
        # 按日期排序
        today_news.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
        
        return today_news[:limit]
        all_news.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
        
        return all_news[:limit * len(symbols)]
    
    def _get_news_for_symbol(self, symbol: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        获取单个股票的新闻
        """
        params = {
            "apikey": self.api_key,
            "q": symbol,  # 搜索关键词
            "language": "en",  # 英语
            "category": "business",  # 商业财经
            "size": limit
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "success" and data.get("results"):
                news_list = []
                for item in data["results"]:
                    news_list.append({
                        "symbol": symbol,
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "link": item.get("link"),
                        "pubDate": item.get("pubDate"),
                        "source_name": item.get("source_name"),
                        "keywords": item.get("keywords", []),
                    })
                logger.info(f"获取 {symbol} 新闻成功: {len(news_list)} 条")
                return news_list
            else:
                logger.warning(f"获取 {symbol} 新闻失败: {data.get('results', {}).get('message', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"获取 {symbol} 新闻出错: {e}")
            return None
    
    def get_market_news(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
       获取市场新闻 (默认30条，筛选当天新闻)
        
        Args:
            limit: 返回新闻数量 (默认30)
            
        Returns:
            新闻列表 (只返回当天新闻)
        """
        params = {
            "apikey": self.api_key,
            "q": "stock market OR stock OR Wall Street OR NASDAQ",
            "language": "en",
            "category": "business",
            "size": limit
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "success" and data.get("results"):
                news_list = []
                for item in data["results"]:
                    news_list.append({
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "link": item.get("link"),
                        "pubDate": item.get("pubDate"),
                        "source_name": item.get("source_name"),
                        "keywords": item.get("keywords", []),
                    })
                # 筛选当天的新闻
                today_news = [n for n in news_list if self._is_today(n.get('pubDate', ''))]
                logger.info(f"获取市场新闻成功: {len(news_list)} 条, 当天新闻: {len(today_news)} 条")
                return today_news[:limit]
            else:
                logger.warning(f"获取市场新闻失败: {data.get('results', {}).get('message', '未知错误')}")
                return []
                
        except Exception as e:
            logger.error(f"获取市场新闻出错: {e}")
            return []


# 便捷函数
def get_news(api_key: str, symbols: List[str]) -> List[Dict[str, Any]]:
    """快速获取新闻"""
    collector = NewsDataCollector(api_key)
    return collector.get_stock_news(symbols)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("NEWSADATA_KEY", "")
    
    collector = NewsDataCollector(api_key)
    news = collector.get_market_news(10)
    print(f"获取到 {len(news)} 条新闻:")
    for n in news:
        print(f"  - {n.get('title')[:50]}...")
