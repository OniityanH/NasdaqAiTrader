"""
AI 决策大脑 - DeepSeek
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class DeepSeekBrain:
    """DeepSeek AI 决策大脑"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat", save_runs: bool = True):
        """
        初始化
        
        Args:
            api_key: DeepSeek API Key
            base_url: API 端点
            model: 模型名称 (deepseek-chat 或 deepseek-reasoner v3.2)
            save_runs: 是否保存每次运行的 prompt 和输出
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.save_runs = save_runs
        self.runs_dir = "runs"
    
    def make_decision(
        self,
        stock_data: Dict[str, Any],
        risk_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        做交易决策
        
        Args:
            stock_data: 格式化后的股票数据
            risk_config: 风控配置
            
        Returns:
            决策结果
        """
        prompt = self.build_prompt(stock_data, risk_config)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的美股量化交易员，擅长基本面分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            result = response.choices[0].message.content
            decision = self.parse_response(result)
            
            # 保存运行记录
            if self.save_runs:
                self._save_run(stock_data.get('symbol', 'UNKNOWN'), prompt, result, decision)
            
            logger.info(f"AI 决策: {decision}")
            return decision
            
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return {
                "decision": "HOLD",
                "shares": 0,
                "reason": "API调用失败",
                "stop_loss": 0,
                "take_profit": 0,
                "confidence": 0,
                "risk_level": "HIGH",
                "error": str(e)
            }
    
    def build_prompt(self, data: Dict[str, Any], risk_config: Dict[str, Any]) -> str:
        """
        构建决策 Prompt
        """
        # 格式化最近10日行情
        # 这里需要从数据中获取，实际使用时会传入
        price_history = data.get('price_history', [])
        price_table = self._format_price_history(price_history)
        
        prompt = f"""# 角色
你是一个专业的美股量化交易员，擅长基本面分析。你需要根据以下数据做出理性的买入/卖出/持有决策。

## 交易对
{data.get('symbol', 'N/A')}

## 账户资金
- USDT可用余额: ${data.get('cash', 0):,.2f}
- 购买力: ${data.get('buying_power', 0):,.2f}

## 当前持仓 (全部股票)
{self._format_all_positions(data.get('all_positions', []))}

## 持仓状态 (当前交易对)
- 当前持仓: {data.get('position_qty', 0):.4f} 股
- 开仓价格: ${data.get('avg_entry_price', 0):.2f}
- 当前盈亏: {data.get('unrealized_pl_pct', 0):.2f}%
- 持仓价值: ${data.get('position_value', 0):,.2f}

## 📈 价格数据 (最近10个交易日)
{price_table}

## 🏢 公司基本面
- 公司名称: {data.get('company_name', 'N/A')}
- 市值: {data.get('market_cap_formatted', 'N/A')}
- 市盈率 (PE): {data.get('pe_ratio', 'N/A')}
- 每股收益 (EPS): ${data.get('eps', 'N/A')}
- 52周最高: ${data.get('week52_high', 0):.2f}
- 52周最低: ${data.get('week52_low', 0):.2f}
- 当前价格 vs 52周: {data.get('price_vs_52w', 'N/A')}
- 目标价: ${data.get('price_target', 'N/A')}
- 分析师评级: {data.get('analyst_rating', 'N/A')} ({data.get('num_analysis', 0)} 家机构)

## 新闻 ({data.get('news_count', 0)} 条)
{data.get('news_summary', '无新闻')}

## ⚠️ 风控参数
- 最大止损: {risk_config.get('stop_loss', 0.20) * 100}%
- 止盈目标: {risk_config.get('take_profit', 0.30) * 100}%
- 单股最大仓位: {risk_config.get('max_position', 0.20) * 100}%
- 每次交易最大仓位: {risk_config.get('max_trade', 0.10) * 100}%
- 每次交易最大金额: $10000

## 📋 输出格式
请严格按照以下JSON格式输出决策 (只输出JSON，不要其他内容):
```json
{{
  "decision": "BUY|SELL|HOLD",
  "shares": 10,
  "reason": "决策理由(30字内)",
  "stop_loss": 169.58,
  "take_profit": 205.28,
  "confidence": 0.85,
  "risk_level": "LOW|MEDIUM|HIGH"
}}
```
"""
        return prompt
    
    def _format_all_positions(self, positions: List[Dict]) -> str:
        """格式化所有持仓"""
        if not positions:
            return "当前无持仓"
        
        lines = ["| 股票 | 数量 | 成本价 | 当前价 | 盈亏 |", "|------|------|--------|--------|------|"]
        for p in positions:
            symbol = p.get('symbol', '')
            qty = p.get('qty', 0)
            avg_price = p.get('avg_entry_price', 0)
            current_price = p.get('current_price', 0)
            pl_pct = p.get('unrealized_pl_pct', 0) * 100
            lines.append(f"| {symbol} | {qty} | ${avg_price:.2f} | ${current_price:.2f} | {pl_pct:+.2f}% |")
        
        return "\n".join(lines)
    
    def _save_run(self, symbol: str, prompt: str, raw_response: str, decision: Dict):
        """保存运行记录到 runs 文件夹"""
        try:
            os.makedirs(self.runs_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.runs_dir}/{timestamp}_{symbol}.json"
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "prompt": prompt,
                "raw_response": raw_response,
                "decision": decision
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"运行记录已保存: {filename}")
        except Exception as e:
            logger.error(f"保存运行记录失败: {e}")
    
    def _format_price_history(self, price_history: List[Dict]) -> str:
        """格式化价格历史为表格"""
        if not price_history:
            return "无历史数据"
        
        lines = ["| 日期 | 开盘价 | 收盘价 |", "|------|--------|--------|"]
        for item in price_history[:10]:
            date = item.get('date', '')
            open_p = item.get('open', 0)
            close_p = item.get('close', 0)
            lines.append(f"| {date} | {open_p:.2f} | {close_p:.2f} |")
        
        return "\n".join(lines)
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析 AI 响应
        """
        try:
            # 尝试提取 JSON
            # 去掉 markdown 代码块标记
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            
            # 确保必要字段存在
            return {
                "decision": data.get("decision", "HOLD"),
                "shares": data.get("shares", 0),
                "reason": data.get("reason", ""),
                "stop_loss": data.get("stop_loss", 0),
                "take_profit": data.get("take_profit", 0),
                "confidence": data.get("confidence", 0),
                "risk_level": data.get("risk_level", "MEDIUM"),
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}, response: {response}")
            return {
                "decision": "HOLD",
                "shares": 0,
                "reason": "解析失败",
                "stop_loss": 0,
                "take_profit": 0,
                "confidence": 0,
                "risk_level": "HIGH",
                "raw_response": response
            }
    
    def analyze_sentiment(self, news_list: list) -> str:
        """
        分析新闻情绪
        """
        if not news_list:
            return "neutral"
        
        keywords_positive = [
            "beat", "surge", "gain", "rise", "growth", "upgrade",
            "buy", "bullish", "profit", "record", "high", "upgrade",
            "exceed", "outperform", "boost", "success"
        ]
        
        keywords_negative = [
            "miss", "fall", "drop", "decline", "downgrade", "sell",
            "bearish", "loss", "low", "warning", "concern", "risk",
            "investigate", "lawsuit", "fraud", "scandal"
        ]
        
        text = " ".join([
            n.get("title", "").lower() + " " + n.get("text", "").lower()
            for n in news_list[:5]
        ])
        
        pos_count = sum(1 for kw in keywords_positive if kw in text)
        neg_count = sum(1 for kw in keywords_negative if kw in text)
        
        if pos_count > neg_count + 1:
            return "bullish"
        elif neg_count > pos_count + 1:
            return "bearish"
        else:
            return "neutral"


# 便捷函数
def make_trading_decision(
    api_key: str,
    stock_data: Dict[str, Any],
    risk_config: Dict[str, Any]
) -> Dict[str, Any]:
    """快速做决策"""
    brain = DeepSeekBrain(api_key)
    return brain.make_decision(stock_data, risk_config)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 测试
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        brain = DeepSeekBrain(api_key)
        
        # 测试数据
        test_data = {
            "symbol": "AAPL",
            "current_price": 178.50,
            "price_change_pct": 2.35,
            "cash": 10000,
            "buying_power": 10000,
            "position_qty": 0,
            "company_name": "Apple Inc.",
            "market_cap_formatted": "2.78T",
            "pe_ratio": 28.50,
            "eps": 6.26,
            "week52_high": 199.62,
            "week52_low": 164.08,
            "price_target": 210.00,
            "analyst_rating": "Buy",
            "num_analysis": 25,
            "beta": 1.28,
            "news_count": 3,
            "news_summary": "1. Apple AI新功能发布\n2. Q4财报超预期\n3. 欧盟调查App Store",
        }
        
        risk_config = {
            "stop_loss": 0.05,
            "take_profit": 0.15,
            "max_position": 0.20,
            "max_trade": 0.10,
            "risk_preference": "conservative",
        }
        
        decision = brain.make_decision(test_data, risk_config)
        print(f"决策结果: {decision}")
    else:
        print("请配置 DEEPSEEK_API_KEY")
