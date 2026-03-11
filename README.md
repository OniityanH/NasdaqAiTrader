# Nasdaq AI Trader 项目架构

## 📋 项目概述

一个自动化美股交易系统，通过整合多源数据 + AI 决策 + 自动下单来执行量化交易策略。

---

## 🏗️ 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Nasdaq AI Trader                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   数据采集层  │    │   AI 决策层   │    │   交易执行层  │             │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤             │
│  │  1. 股票行情  │    │              │    │              │             │
│  │  2. 订单流    │───▶│  DeepSeek    │───▶│   Alpaca     │             │
│  │  3. 新闻资讯  │    │  决策大脑    │    │   交易API    │             │
│  │              │    │              │    │              │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                     数据总线 (Data Bus)                       │       │
│  │              JSON / Pandas DataFrame / SQLite               │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 API 数据源设计

### 1. 股票行情数据 (价格 + 历史)

| API | 用途 | 费用 | 数据类型 |
|-----|------|------|----------|
| **Alpha Vantage** | 基础行情 + 历史K线 | 免费(25次/天) | OHLCV, 技术指标, NASDAQ官方合作 |
| **FMP** (Financial Modeling Prep) | 基本面 + 新闻 | 免费(250次/天) | 财务数据, 新闻, 舆情 |
| **Alpaca Market Data** | 实时/历史行情 | 免费(有限制) | OHLCV, 当日数据 |

**推荐方案**: `Alpha Vantage` (免费实时) + `FMP` (基本面/新闻)

```python
# Alpha Vantage 示例
import requests

API_KEY = "YOUR_ALPHA_VANTAGE_KEY"
symbol = "AAPL"

# 获取实时价格
url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
response = requests.get(url).json()
price = response['Global Quote']['05. price']

# 获取历史K线 (Technical Indicators)
url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
```

```python
# FMP 获取新闻
import requests

API_KEY = "YOUR_FMP_KEY"
symbol = "AAPL"

# 获取新闻
url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={symbol}&limit=10&apikey={API_KEY}"
news = requests.get(url).json()
```

### 2. 订单流/交易动态数据

| API | 用途 | 费用 |
|-----|------|------|
| **Alpaca** | 账户持仓、订单状态 | 免费 |
| **Polygon.io** | 实时成交流(Trade) | 付费 |
| **FMP (Financial Modeling Prep)** | 大单追踪、机构持仓 | 付费 |

**推荐方案**: Alpaca 获取持仓 + yfinance 获取成交量/大单数据

```python
# Alpaca 账户信息
from alpaca.trading.client import TradingClient
client = TradingClient('API_KEY', 'SECRET_KEY', paper=True)
account = client.get_account()
positions = client.get_all_positions()
```

### 3. 新闻数据

| API | 用途 | 费用 |
|-----|------|------|
| **Alpaca News** | 股票相关新闻 | 免费 |
| **FMP News** | 实时新闻+舆情 | 付费 |
| **NewsAPI** | 通用新闻API | 免费/付费 |
| **Yahoo Finance** | 新闻标题 | 免费 |

**推荐方案**: `Alpaca News` (免费且直接集成) + `yfinance` 新闻

```python
# Alpaca 获取新闻
from alpaca.data.news import NewsClient
news_client = NewsClient('API_KEY')
news = news_client.get_news(symbols=['AAPL', 'NVDA'], limit=10)
```

---

## 🔄 数据流设计

### 模块间数据传输格式

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  DataCollector │ ───▶ │   DataBus       │ ───▶ │  DeepSeek Brain │
│                 │      │                 │      │                 │
│ 返回: Dict      │      │ 存储: SQLite   │      │ 输入: Prompt    │
│ - price         │      │ 格式: JSON      │      │ 输出: Decision  │
│ - volume        │      │                 │      │                 │
│ - news          │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                            │
                                                            ▼
                                                   ┌─────────────────┐
                                                   │  Alpaca Trader  │
                                                   │                 │
                                                   │ 执行: buy/sell  │
                                                   │ 返回: order_id  │
                                                   └─────────────────┘
```

### 核心数据结构

```python
# StockData 模型
class StockData:
    symbol: str              # 股票代码: "AAPL"
    current_price: float     # 当前价格
    price_change_pct: float  # 涨跌幅 %
    
    # 基本面数据 (from FMP)
    market_cap: float        # 市值
    pe_ratio: float         # 市盈率
    eps: float              # 每股收益
    week52_high: float      # 52周最高
    week52_low: float       # 52周最低
    price_target: float     # 目标价
    analyst_rating: str     # 分析师评级
    beta: float             # Beta值
    
    # 订单流
    volume: int              # 成交量
    avg_volume: float        # 平均成交量
    volume_ratio: float      # 量比
    
    # 持仓/资金
    position: int            # 当前持仓数量
    avg_entry_price: float   # 平均持仓成本
    unrealized_pl: float     # 未实现盈亏
    
    # 新闻
    news: List[NewsItem]     # 最新新闻列表
```

---

## 🤖 DeepSeek 决策模块

### 📝 完整示例 Prompt

```python
# 示例：让 DeepSeek 决策 AAPL 是否买入

EXAMPLE_PROMPT = """
# 角色
你是一个专业的美股量化交易员，擅长基本面分析。你需要根据以下数据做出理性的买入/卖出/持有决策。

## 交易对
AAPL

## 账户资金
- USDT可用余额: $10,000.00

## 持仓状态
- 当前持仓: 0 股
- 开仓价格: $0.00
- 当前盈亏: 0%
- 持仓时间: 0小时

## 📈 价格数据 (Alpha Vantage)
- 当前价格: $178.50
- 24h涨跌: +2.35%
- 24h最高: $179.80
- 24h最低: $173.90
- 24h成交量: 52,430,000

## 📈 价格数据 (最近10个交易日)
| 日期 | 开盘价 | 收盘价 |
|------|--------|--------|
| 03-11 | 174.20 | 178.50 |
| 03-10 | 171.50 | 174.20 |
| 03-09 | 175.00 | 171.50 |
| 03-08 | 172.80 | 175.00 |
| 03-07 | 170.00 | 172.80 |
| 03-06 | 168.50 | 170.00 |
| 03-05 | 165.00 | 168.50 |
| 03-04 | 162.30 | 165.00 |
| 03-03 | 160.00 | 162.30 |
| 02-28 | 158.50 | 160.00 |

## 🏢 公司基本面 (FMP)
- 公司名称: Apple Inc.
- 市值: 2.78T
- 市盈率 (PE): 28.50
- 每股收益 (EPS): $6.26
- 52周最高: $199.62
- 52周最低: $164.08
- 目标价: $210.00
- 分析师评级: Buy (25 家机构)
- Beta: 1.28

## 📰 新闻 (最近3条)
1. [正面] Apple announces new AI features for iPhone, boosting investor confidence
2. [正面] Apple reports record Q4 earnings, revenue exceeds expectations
3. [中性] Regulatory concerns grow as EU investigates App Store policies

## 综合情绪: bullish

## ⚠️ 风控参数
- 最大止损: 20%
- 止盈目标: 30%
- 单股最大仓位: 20%
- 每次交易最大仓位: 10%

## 📋 输出格式
请严格按照以下JSON格式输出决策:
```json
{
  "decision": "BUY|SELL|HOLD",
  "shares": 10,
  "reason": "决策理由(30字内)",
  "stop_loss": 169.58,
  "take_profit": 205.28,
  "confidence": 0.85,
  "risk_level": "LOW|MEDIUM|HIGH"
}
```
"""
```

### 示例输出 (DeepSeek 返回)

```json
{
  "decision": "BUY",
  "shares": 5,
  "reason": "AI新功能+业绩超预期，目标价空间大",
  "stop_loss": 169.58,
  "take_profit": 205.28,
  "confidence": 0.80,
  "risk_level": "MEDIUM"
}
```

```python
TRADING_PROMPT = """
# 角色
你是一个专业的美股量化交易员，擅长基本面分析。你需要根据以下数据做出理性的买入/卖出/持有决策。

## 📈 市场数据 (Alpha Vantage)
- 当前价格: ${current_price}
- 涨跌幅: {price_change_pct}%
- 今日开盘: ${open}
- 今日最高: ${high}
- 今日最低: ${low}
- 成交量: {volume}

## 🏢 公司基本面 (FMP)
- 公司名称: {company_name}
- 市值: ${market_cap} ({market_cap_formatted})
- 市盈率 (PE): {pe_ratio}
- 每股收益 (EPS): ${eps}
- 52周最高: ${week52_high}
- 52周最低: ${week52_low}
- 当前价格 vs 52周高低: {price_vs_52w}%
- 目标价: ${price_target}
- 分析师评级: {analyst_rating} ({num_analysis} 家机构)
- Beta: {beta}

## 📰 最新新闻 ({news_count} 条)
{news_summary}

## 💼 账户状况
- 现金余额: ${cash}
- 购买力: ${buying_power}
- 持仓: {symbol} = {position} 股
- 持仓成本: ${avg_entry_price}
- 当前价值: ${position_value}
- 未实现盈亏: ${unrealized_pl} ({pl_pct}%)

## ⚠️ 交易规则 (必须遵守)
1. 止损: 亏损 ≥5% 强制卖出
2. 止盈: 盈利 ≥15% 建议分批卖出
3. 仓位: 单股 ≤20%, 每次 ≤10% 资金
4. 风控: 单日亏损 ≥3% 停止交易

## 📋 输出格式
请严格按照以下JSON格式输出决策:
```json
{
  "decision": "BUY|SELL|HOLD",
  "shares": 10,
  "reason": "决策理由(30字内)",
  "stop_loss": 145.50,
  "take_profit": 175.00,
  "confidence": 0.85,
  "risk_level": "LOW|MEDIUM|HIGH"
}
```
"""
```

### FMP API 关键字段映射

| FMP 字段 | 说明 |
|----------|------|
| `marketCap` | 市值 |
| `priceAvg50` | 50日均 |
| `priceAvg200` | 200日均 |
| `beta` | Beta值 |
| `priceAvg` | 当前价格 |
| `priceTarget` | 目标价 |
| `numberOfAnalysts` | 分析师数 |
| `rating` | 评级 |

### 决策逻辑示例

```
PE过低(<0或过高>50) → 谨慎
市值>万亿 + PE合理 → 稳健
目标价 > 当前价 20% → 可能上涨空间大
新闻情绪偏负面 → 谨慎买入
已有盈利≥15% → 考虑止盈
亏损≥5% → 强制止损
```

---

## 📁 项目目录结构

```
Nasdaq_ai_trader/
├── venv/                      # Python 虚拟环境
│
├── config/
│   ├── api_keys.yaml          # API 密钥配置
│   └── settings.yaml          # 交易参数配置
│
├── src/
│   ├── data_collector/
│   │   ├── __init__.py
│   │   ├── market_data.py     # 行情数据采集 (yfinance)
│   │   ├── alpaca_data.py    # Alpaca 账户/持仓数据
│   │   └── news_collector.py # 新闻采集
│   │
│   ├── data_bus/
│   │   ├── __init__.py
│   │   └── data_manager.py   # 数据总线 + SQLite存储
│   │
│   ├── ai_brain/
│   │   ├── __init__.py
│   │   ├── deepseek_client.py # DeepSeek API 调用
│   │   ├── prompt_builder.py  # Prompt 构建器
│   │   └── decision_parser.py # 决策结果解析
│   │
│   ├── trader/
│   │   ├── __init__.py
│   │   ├── alpaca_trader.py  # Alpaca 交易执行
│   │   └── order_manager.py  # 订单管理
│   │
│   └── scheduler/
│       ├── __init__.py
│       └── trading_loop.py   # 交易循环调度
│
├── logs/                      # 日志目录
├── data/                      # 数据缓存目录
├── main.py                    # 入口文件
└── requirements.txt           # 依赖列表
```

---

## 🔌 核心 API 接口设计

### 1. 数据采集接口

```python
# src/data_collector/market_data.py
class MarketDataCollector:
    def get_current_price(self, symbol: str) -> float
    def get_historical_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame
    def get_volume_data(self, symbol: str) -> dict  # 成交量、量比
    def get_technical_indicators(self, symbol: str) -> dict  # RSI, MACD, MA
```

```python
# src/data_collector/news_collector.py
class NewsCollector:
    def get_stock_news(self, symbols: List[str], limit: int = 10) -> List[NewsItem]
    def get_market_news(self) -> List[NewsItem]
```

### 2. 数据总线接口

```python
# src/data_bus/data_manager.py
class DataManager:
    def collect_all_data(self, symbols: List[str]) -> StockDataBundle
    def save_to_cache(self, data: StockDataBundle)
    def load_from_cache(self, symbol: str) -> Optional[StockDataBundle]
```

### 3. AI 决策接口

```python
# src/ai_brain/deepseek_client.py
class DeepSeekBrain:
    def make_decision(self, stock_data: StockDataBundle) -> TradingDecision
    def build_prompt(self, stock_data: StockDataBundle) -> str
    def parse_response(self, response: str) -> TradingDecision
```

### 4. 交易执行接口

```python
# src/trader/alpaca_trader.py
class AlpacaTrader:
    def get_account_info(self) -> AccountInfo
    def get_positions(self) -> List[Position]
    def place_order(self, symbol: str, qty: int, side: str, order_type: str = "market") -> Order
    def place_limit_order(self, symbol: str, qty: int, side: str, limit_price: float) -> Order
    def cancel_order(self, order_id: str)
    def set_stop_loss(self, symbol: str, stop_price: float)
```

---

## ⚙️ 依赖列表 (requirements.txt)

```text
# 数据采集
alphavantage>=1.3.0
financialmodelingprep>=4.0.0
alpaca-py>=0.15.0
requests>=2.31.0

# AI
openai>=1.12.0  # DeepSeek 兼容 OpenAI API 格式

# 数据处理
pandas>=2.0.0
numpy>=1.24.0

# 存储
sqlalchemy>=2.0

# 工具
python-dotenv>=1.0.0
pyyaml>=6.0
logging (内置)

# 可选(高级)
# polygon-io>=1.5.0  # 付费行情
# ta-lib>=0.4.28    # 技术指标
```

---

## 🚀 交易流程

```
1. 启动 scheduler/trading_loop.py

2. 获取监控股票列表 (config/settings.yaml)
   symbols = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"]

3. 遍历每只股票:
   │
   ├─▶ DataCollector 采集数据
   │   ├─ yfinance: 价格、历史K线、成交量
   │   ├─ Alpaca: 持仓、成本价
   │   └─ Alpaca/Yahoo: 新闻
   │
   ├─▶ DataManager 整合数据
   │   └─ 构建 StockDataBundle
   │
   ├─▶ DeepSeekBrain 决策
   │   ├─ 构建 Prompt
   │   ├─ 调用 DeepSeek API
   │   └─ 解析决策结果
   │
   └─▶ AlpacaTrader 执行
       ├─ BUY: 检查资金 → 下单 → 设置止损
       ├─ SELL: 检查持仓 → 下单
       └─ HOLD: 记录日志

4. 等待下一个周期 (默认 5 分钟)
```

---

## ⚠️ 风险控制

| 规则 | 说明 |
|------|------|
| 止损 | 单笔亏损 ≥5% 强制止损 |
| 止盈 | 盈利 ≥15% 考虑分批止盈 |
| 仓位 | 单只股票 ≤20% 仓位 |
| 仓位 | 每次交易 ≤10% 资金 |
| 验证 | 全部使用 Paper Trading 模拟盘测试 |
| 风控 | 单日最大亏损 3% 停止交易 |

---

## 📝 下一步

1. **配置 API 密钥** → 在 `config/api_keys.yaml` 填写
2. **安装依赖** → `pip install -r requirements.txt`
3. **测试数据采集** → 运行 `src/data_collector/` 各模块
4. **测试 AI 决策** → 单独调用 DeepSeek 测试
5. **模拟盘测试** → Alpaca Paper Trading 实盘验证

---

*架构版本: v1.0*  
*创建日期: 2026-03-11*
