"""
数据总线 - 整合所有数据源
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..data_collector.market_data import MarketDataCollector
from ..data_collector.fundamental_data import FundamentalDataCollector
from ..data_collector.alpaca_data import AlpacaDataCollector
from ..data_collector.newsdata_collector import NewsDataCollector
from ..data_collector.yfinance_collector import YFinanceCollector

logger = logging.getLogger(__name__)


class DataBus:
    """
    数据总线 - 整合市场数据、基本面数据、持仓数据
    """
    
    def __init__(
        self,
        alpha_vantage_key: str,
        fmp_key: str,
        alpaca_api_key: str,
        alpaca_secret_key: str,
        alpaca_paper: bool = True,
        newsdata_key: str = ""
    ):
        """初始化所有数据采集器"""
        self.market_collector = MarketDataCollector(alpha_vantage_key)
        self.fundamental_collector = FundamentalDataCollector(fmp_key)
        self.alpaca_collector = AlpacaDataCollector(
            alpaca_api_key, 
            alpaca_secret_key, 
            alpaca_paper
        )
        # 新闻采集器
        self.news_collector = NewsDataCollector(newsdata_key) if newsdata_key else None
        
        # yfinance 采集器 (备用)
        self.yfinance_collector = YFinanceCollector()
        
        # 缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = 60  # 缓存60秒
    
    def get_stock_data(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取单只股票的所有数据
        
        Args:
            symbol: 股票代码
            use_cache: 是否使用缓存
            
        Returns:
            整合后的股票数据
        """
        # 检查缓存
        if use_cache and self._is_cached(symbol):
            logger.info(f"使用缓存数据: {symbol}")
            return self._cache[symbol]
        
        yf_data = self.yfinance_collector.get_all_data(symbol)
        if yf_data:
            fundamental_data = yf_data
            # 用yfinance的quote更新market数据
            if yf_data.get("quote"):
                market_data = yf_data["quote"]
        
        news_data = []
        
        # 4. 获取持仓数据 (Alpaca)
        # 先获取所有持仓，再从中查找当前股票的持仓
        all_positions_list = self.alpaca_collector.get_positions()
        
        # 查找当前股票的持仓
        position = None
        for p in all_positions_list:
            if p.get('symbol') == symbol:
                position = p
                break
        
        # 5. 获取账户数据 (Alpaca)
        account = self.alpaca_collector.get_account()
        
        # 整合数据
        stock_data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            
            # 市场数据
            "market": market_data or {},
            
            # 基本面数据
            "fundamental": fundamental_data,
            
            # 新闻数据
            "news": news_data,
            
            # 持仓数据
            "position": position,
            
            # 账户数据
            "account": account,
            
            # 所有持仓列表
            "all_positions_raw": all_positions_list,
        }
        
        # 更新缓存
        self._cache[symbol] = stock_data
        self._cache_time[symbol] = datetime.now()
        
        return stock_data
    
    def get_watchlist_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        获取监控列表中所有股票的数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            所有股票数据列表
        """
        results = []
        
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol)
                results.append(data)
            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
                continue
        
        return results
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        获取账户摘要
        """
        return self.alpaca_collector.get_account_summary()
    
    def get_news(self, symbols: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取股票新闻
        
        Args:
            symbols: 股票代码列表，None 表示获取市场新闻
            limit: 新闻数量
            
        Returns:
            新闻列表
        """
        if not self.news_collector:
            logger.warning("新闻采集器未初始化")
            return []
        
        if symbols:
            return self.news_collector.get_stock_news(symbols, limit)
        else:
            return self.news_collector.get_market_news(limit)
    
    def _is_cached(self, symbol: str) -> bool:
        """检查缓存是否有效"""
        if symbol not in self._cache:
            return False
        
        if symbol not in self._cache_time:
            return False
        
        elapsed = (datetime.now() - self._cache_time[symbol]).total_seconds()
        return elapsed < self._cache_ttl
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        清除缓存
        
        Args:
            symbol: 指定股票代码，None 表示清除所有
        """
        if symbol:
            self._cache.pop(symbol, None)
            self._cache_time.pop(symbol, None)
        else:
            self._cache.clear()
            self._cache_time.clear()


def format_stock_data_for_ai(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化股票数据为 AI 决策可用的格式
    """
    market = data.get("market", {})
    fundamental = data.get("fundamental", {})
    quote = fundamental.get("quote", {})
    profile = fundamental.get("profile", {})
    rating = fundamental.get("rating", {})
    price_target = fundamental.get("price_target", {})
    news = data.get("news", [])  # 从 stock_data 中获取新闻
    position = data.get("position", {})
    account = data.get("account", {})
    
    # 计算市值格式化
    market_cap = quote.get("marketCap") or profile.get("marketCap")
    market_cap_formatted = _format_market_cap(market_cap) if market_cap else "N/A"
    
    # 计算当前价格 vs 52周
    price = market.get("current_price") or quote.get("price")
    week52_high = quote.get("year_high") or profile.get("priceAvg200")  # 用200日均近似
    week52_low = quote.get("year_low")
    price_vs_52w = "N/A"
    if price and week52_high and week52_low:
        range_size = week52_high - week52_low
        if range_size > 0:
            price_vs_52w = f"{((price - week52_low) / range_size) * 100:.0f}%"
    
    # 格式化新闻
    news_summary = "\n".join([
        f'{i+1}. [{n.get("publishedDate", "")}] {n.get("title", "")}'
        for i, n in enumerate(news[:3])
    ]) if news else "无新闻"
    
    # 计算未实现盈亏
    unrealized_pl = 0.0
    unrealized_pl_pct = 0.0
    if position:
        unrealized_pl = position.get("unrealized_pl", 0)
        unrealized_pl_pct = position.get("unrealized_plpc", 0) * 100
    
    # 计算持仓价值
    position_value = 0
    if position and position.get("current_price"):
        position_value = position["qty"] * position["current_price"]
    
    # 获取所有持仓 (使用已获取的数据)
    all_positions_raw = data.get("all_positions_raw", [])
    
    return {
        # 交易对/股票
        "symbol": data.get("symbol", ""),
        
        # 市场数据
        "current_price": price or 0,
        "price_change_pct": market.get("price_change_pct") or quote.get("changes_percentage") or 0,
        "open": market.get("open") or quote.get("open"),
        "high": market.get("high") or quote.get("day_high"),
        "low": market.get("low") or quote.get("day_low"),
        "volume": market.get("volume") or quote.get("volume"),
        
        # 基本面
        "company_name": profile.get("company_name") or quote.get("name"),
        "market_cap": market_cap or 0,
        "market_cap_formatted": market_cap_formatted,
        "pe_ratio": quote.get("pe") or fundamental.get("metrics", {}).get("pe_ratio"),
        "eps": quote.get("eps") or "N/A",
        "week52_high": week52_high or 0,
        "week52_low": week52_low or 0,
        "price_vs_52w": price_vs_52w,
        "price_target": price_target.get("price_target_avg") or "N/A",
        "analyst_rating": rating.get("rating") or price_target.get("rating") or "N/A",
        "num_analysis": rating.get("total_analysts") or price_target.get("total_analysts") or 0,
        "beta": profile.get("beta") or 1.0,
        
        # 新闻
        "news_count": len(news),
        "news_summary": news_summary,
        
        # 账户/持仓
        "cash": account.get("cash", 0) if account else 0,
        "buying_power": account.get("buying_power", 0) if account else 0,
        "position_qty": position.get("qty", 0) if position else 0,
        "avg_entry_price": position.get("avg_entry_price", 0) if position else 0,
        "position_value": position_value,
        "unrealized_pl": unrealized_pl,
        "unrealized_pl_pct": unrealized_pl_pct,
        
        # 全部持仓
        "all_positions": all_positions_raw,
    }


def _format_market_cap(cap: int) -> str:
    """格式化市值"""
    if cap >= 1_000_000_000_000:
        return f"${cap / 1_000_000_000_000:.2f}T"
    elif cap >= 1_000_000_000:
        return f"${cap / 1_000_000_000:.2f}B"
    elif cap >= 1_000_000:
        return f"${cap / 1_000_000:.2f}M"
    else:
        return f"${cap}"


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 测试
    data_bus = DataBus(
        alpha_vantage_key=os.getenv("ALPHA_VANTAGE_KEY", "demo"),
        fmp_key=os.getenv("FMP_KEY", "demo"),
        alpaca_api_key=os.getenv("ALPAPACA_API_KEY", ""),
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY", ""),
    )
    
    # 获取 AAPL 数据
    aapl_data = data_bus.get_stock_data("AAPL")
    formatted = format_stock_data_for_ai(aapl_data)
    print(formatted)
