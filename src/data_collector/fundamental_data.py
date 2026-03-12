"""
数据采集器 - 公司基本面数据
使用 FMP (Financial Modeling Prep) API 获取基本面数据
"""
import requests
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class FundamentalDataCollector:
    """FMP 基本面数据采集器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def get_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取公司基本信息
        
        Returns:
            包含公司基本信息的字典
        """
        url = f"{self.base_url}/profile/{symbol}"
        params = {"apikey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # 检查是否返回错误信息
            if isinstance(data, dict) and "Error Message" in data:
                logger.warning(f"FMP API错误: {data.get('Error Message')}")
                return None
            
            if data and isinstance(data, list) and len(data) > 0:
                profile = data[0]
                return {
                    "symbol": profile.get("symbol"),
                    "company_name": profile.get("companyName"),
                    "currency": profile.get("currency"),
                    "cusip": profile.get("cusip"),
                    "isin": profile.get("isin"),
                    "exchange": profile.get("exchange"),
                    "ipo": profile.get("ipoDate"),
                    "close": profile.get("price"),
                    "price_avg_50": profile.get("priceAvg50"),
                    "price_avg_200": profile.get("priceAvg200"),
                    "market_cap": profile.get("marketCap"),
                    "beta": profile.get("beta"),
                    "vol_avg": profile.get("volAvg"),
                    "mfd_vol_date": profile.get("mfdVolDate"),
                    "mfd_vol": profile.get("mfdVol"),
                }
            return None
            
        except Exception as e:
            logger.error(f"获取 {symbol} 基本信息失败: {e}")
            return None
    
    def get_key_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取关键财务指标
        """
        url = f"{self.base_url}/key-metrics/{symbol}"
        params = {
            "apikey": self.api_key,
            "limit": 1  # 最新一期
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # 检查是否返回错误信息
            if isinstance(data, dict) and "Error Message" in data:
                logger.warning(f"FMP API错误: {data.get('Error Message')}")
                return None
            
            if data and isinstance(data, list) and len(data) > 0:
                metrics = data[0]
                return {
                    "symbol": metrics.get("symbol"),
                    "pe_ratio": metrics.get("peRatio"),
                    "peg_ratio": metrics.get("pegRatio"),
                    "payout_ratio": metrics.get("payoutRatio"),
                    "current_ratio": metrics.get("currentRatio"),
                    "quick_ratio": metrics.get("quickRatio"),
                    "cash_ratio": metrics.get("cashRatio"),
                    "days_of_sales_outstanding": metrics.get("daysOfSalesOutstanding"),
                    "days_of_inventory_outstanding": metrics.get("daysOfInventoryOutstanding"),
                    "operating_cycle": metrics.get("operatingCycle"),
                    "days_of_payables_outstanding": metrics.get("daysOfPayablesOutstanding"),
                    "cash_conversion_cycle": metrics.get("cashConversionCycle"),
                    "gross_profit_margin": metrics.get("grossProfitMargin"),
                    "operating_profit_margin": metrics.get("operatingProfitMargin"),
                    "pretax_profit_margin": metrics.get("pretaxProfitMargin"),
                    "net_profit_margin": metrics.get("netProfitMargin"),
                    "effective_tax_rate": metrics.get("effectiveTaxRate"),
                    "return_on_assets": metrics.get("returnOnAssets"),
                    "return_on_equity": metrics.get("returnOnEquity"),
                    "return_on_capital_employed": metrics.get("returnOnCapitalEmployed"),
                    "net_income_per_ebt": metrics.get("netIncomePerEBT"),
                    "ebt_per_ebit": metrics.get("ebtPerEbit"),
                    "ebit_per_revenue": metrics.get("ebitPerRevenue"),
                    "debt_ratio": metrics.get("debtRatio"),
                    "debt_equity_ratio": metrics.get("debtEquityRatio"),
                    "long_term_debt_to_capitalization": metrics.get("longTermDebtToCapitalization"),
                    "total_debt_to_capitalization": metrics.get("totalDebtToCapitalization"),
                    "interest_coverage": metrics.get("interestCoverage"),
                    "cash_flow_to_debt_ratio": metrics.get("cashFlowToDebtRatio"),
                    "company_equity": metrics.get("companyEquity"),
                    "total_liabilities": metrics.get("totalLiabilities"),
                    "total_current_liabilities": metrics.get("totalCurrentLiabilities"),
                    "total_assets": metrics.get("totalAssets"),
                    "total_current_assets": metrics.get("totalCurrentAssets"),
                    "cash_and_equivalents": metrics.get("cashAndEquivalents"),
                    "operating_cash_flow": metrics.get("operatingCashFlow"),
                    "capex": metrics.get("capex"),
                }
            return None
            
        except Exception as e:
            logger.error(f"获取 {symbol} 关键指标失败: {e}")
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取实时报价 (FMP)
        """
        url = f"{self.base_url}/quote/{symbol}"
        params = {"apikey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # 检查是否返回错误信息
            if isinstance(data, dict) and "Error Message" in data:
                logger.warning(f"FMP API错误: {data.get('Error Message')}")
                return None
            
            if data and isinstance(data, list) and len(data) > 0:
                quote = data[0]
                return {
                    "symbol": quote.get("symbol"),
                    "name": quote.get("name"),
                    "price": quote.get("price"),
                    "changes_percentage": quote.get("changesPercentage"),
                    "change": quote.get("change"),
                    "day_low": quote.get("dayLow"),
                    "day_high": quote.get("dayHigh"),
                    "year_high": quote.get("yearHigh"),
                    "year_low": quote.get("yearLow"),
                    "market_cap": quote.get("marketCap"),
                    "price_avg_50": quote.get("priceAvg50"),
                    "price_avg_200": quote.get("priceAvg200"),
                    "volume": quote.get("volume"),
                    "avg_volume": quote.get("avgVolume"),
                    "exchange": quote.get("exchange"),
                    "open": quote.get("open"),
                    "previous_close": quote.get("previousClose"),
                    "eps": quote.get("eps"),
                    "pe": quote.get("pe"),
                }
            return None
            
        except Exception as e:
            logger.error(f"获取 {symbol} 报价失败: {e}")
            return None
    
    def get_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取股票新闻
        """
        url = f"{self.base_url}/stock_news"
        params = {
            "tickers": symbol,
            "limit": limit,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if isinstance(data, list):
                return [
                    {
                        "symbol": item.get("symbol"),
                        "published_date": item.get("publishedDate"),
                        "title": item.get("title"),
                        "image": item.get("image"),
                        "site": item.get("site"),
                        "text": item.get("text"),
                    }
                    for item in data
                ]
            return []
            
        except Exception as e:
            logger.error(f"获取 {symbol} 新闻失败: {e}")
            return []
    
    def get_price_target(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取分析师价格目标
        """
        url = f"{self.base_url}/price-target"
        params = {
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # 检查是否返回错误信息
            if isinstance(data, dict) and "Error Message" in data:
                logger.warning(f"FMP API错误: {data.get('Error Message')}")
                return None
            
            if data and isinstance(data, list) and len(data) > 0:
                latest = data[0]  # 最新目标价
                return {
                    "symbol": latest.get("symbol"),
                    "price_target_avg": latest.get("priceTargetAverage"),
                    "price_target_high": latest.get("priceTargetHigh"),
                    "price_target_low": latest.get("priceTargetLow"),
                    "number_of_analysts": latest.get("numberOfAnalysts"),
                    "rating_avg": latest.get("ratingAverage"),
                }
            return None
            
        except Exception as e:
            logger.error(f"获取 {symbol} 目标价失败: {e}")
            return None
    
    def get_rating(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取分析师评级
        """
        url = f"{self.base_url}/rating/{symbol}"
        params = {"apikey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # 检查是否返回错误信息
            if isinstance(data, dict) and "Error Message" in data:
                logger.warning(f"FMP API错误: {data.get('Error Message')}")
                return None
            
            if data and isinstance(data, list) and len(data) > 0:
                rating = data[0]
                return {
                    "symbol": rating.get("symbol"),
                    "rating": rating.get("rating"),
                    "rating_score": rating.get("ratingScore"),
                    "rating_recommendation": rating.get("ratingRecommendation"),
                    "total_analysts": rating.get("totalAnalysts"),
                }
            return None
            
        except Exception as e:
            logger.error(f"获取 {symbol} 评级失败: {e}")
            return None
    
    def get_all_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取该股票的所有数据 (组合调用)
        """
        result = {
            "symbol": symbol,
            "timestamp": None
        }
        
        # 基本信息
        profile = self.get_profile(symbol)
        if profile:
            result["profile"] = profile
        
        # 报价
        quote = self.get_quote(symbol)
        if quote:
            result["quote"] = quote
        
        # 关键指标
        metrics = self.get_key_metrics(symbol)
        if metrics:
            result["metrics"] = metrics
        
        # 新闻
        news = self.get_news(symbol, limit=5)
        if news:
            result["news"] = news
        
        # 目标价
        price_target = self.get_price_target(symbol)
        if price_target:
            result["price_target"] = price_target
        
        # 评级
        rating = self.get_rating(symbol)
        if rating:
            result["rating"] = rating
        
        return result


# 便捷函数
def get_fundamental_data(symbol: str, fmp_key: str) -> Dict[str, Any]:
    """快速获取基本面数据"""
    collector = FundamentalDataCollector(fmp_key)
    return collector.get_all_data(symbol)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("FMP_KEY", "demo")
    
    collector = FundamentalDataCollector(api_key)
    data = collector.get_all_data("AAPL")
    print(f"AAPL 基本面数据: {data}")
