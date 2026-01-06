# 加密货币量化平台改造说明

## 改造概述

本文档说明将ZQuant从股票量化平台改造为币圈量化平台的详细方案。

## 已完成的改造

### 1. 数据模型 ✅

**文件**: `zquant/models/crypto.py`

新增表结构:

| 表名 | 说明 | 关键字段 |
|-----|-----|---------|
| `zq_data_crypto_pairs` | 交易对表 | symbol, base_asset, quote_asset, exchange, status |
| `zq_data_crypto_klines` | K线数据表 | symbol, interval, timestamp, open, high, low, close, volume |
| `zq_data_crypto_tickers` | 实时行情表 | price, price_change, high_24h, low_24h, volume_24h |
| `zq_data_crypto_orderbook` | 订单簿表 | bids_json, asks_json |
| `zq_data_crypto_funding_rates` | 资金费率表 | funding_rate, mark_price, index_price |
| `zq_app_crypto_favorites` | 自选交易对 | user_id, symbol, reason, tags |
| `zq_app_crypto_positions` | 用户持仓表 | symbol, position_type, quantity, leverage, unrealized_pnl |
| `zq_app_crypto_transactions` | 交易记录表 | order_type, order_side, quantity, price, fee, is_maker |
| `zq_app_exchange_configs` | 交易所配置表 | exchange, api_key, api_secret, passphrase |

### 2. 交易所数据源 ✅

**文件结构**:
```
zquant/crypto/
├── exchange_base.py      # 交易所基类(抽象接口)
├── exchange_factory.py   # 交易所工厂(Factory模式)
├── binance.py           # 币安交易所实现
├── okx.py              # OKX交易所实现
├── bybit.py            # Bybit交易所实现
└── __init__.py         # 模块导出
```

**支持的交易所**:
- 币安(Binance) - 现货 + 合约
- OKX - 现货 + 合约
- Bybit - 现货 + 合约

**核心接口**:
```python
class ExchangeBase(ABC):
    def get_exchange_name() -> str
    def get_pairs() -> list[dict]
    def get_ticker(symbol: str) -> dict
    def get_klines(symbol, interval, start_time, end_time, limit) -> pd.DataFrame
    def get_orderbook(symbol, limit) -> dict
    def get_funding_rate(symbol) -> dict
```

### 3. 回测引擎改造 ✅

**文件**:
- `zquant/backtest/crypto_context.py` - 加密货币Context对象
- `zquant/backtest/crypto_cost.py` - 加密货币成本计算器
- `zquant/backtest/crypto_engine.py` - 加密货币回测引擎

**核心改动**:
1. **Context对象**:
   - `current_time`: 改为datetime(精确到秒/毫秒)
   - 增加`exchange_name`: 交易所名称
   - 增加`open_long()`: 开多仓方法
   - 增加`open_short()`: 开空仓方法
   - 增加`close_position()`: 平仓方法

2. **成本计算器**:
   - 支持不同交易所的费率
   - 区分Maker/Taker费率
   - Maker费率: 挂单成交(通常更低)
   - Taker费率: 吃单成交(通常更高)

3. **回测引擎**:
   - T+0即时成交(无交易日历限制)
   - 24/7连续交易
   - 支持多订单类型(market/limit/stop_limit)
   - 支持杠杆交易

### 4. 工厂模式 ✅

**文件**: `zquant/crypto/exchange_factory.py`

```python
class ExchangeFactory:
    @classmethod
    def create_exchange(exchange_name, api_key, api_secret, passphrase) -> ExchangeBase:
        """根据交易所名称创建对应的交易所客户端"""
```

**使用示例**:
```python
from zquant.crypto import ExchangeFactory

# 创建币安交易所
exchange = ExchangeFactory.create_exchange(
    exchange_name="binance",
    api_key="your-api-key",
    api_secret="your-api-secret",
)

# 创建OKX交易所
exchange = ExchangeFactory.create_exchange(
    exchange_name="okx",
    api_key="your-api-key",
    api_secret="your-api-secret",
    passphrase="your-passphrase",  # OKX需要
)
```

### 5. 依赖包 ✅

**文件**: `zquant/requirements_crypto.txt`

新增依赖:
```
ccxt>=4.0.0  # 统一的加密货币交易所SDK
websockets>=13.0  # Websocket(可选,用于实时行情)
```

## 使用示例

### 1. 初始化交易所

```python
from zquant.crypto import ExchangeFactory

# 创建币安交易所
exchange = ExchangeFactory.create_exchange(
    exchange_name="binance",
    api_key="your-api-key",
    api_secret="your-api-secret",
)

# 获取交易对列表
pairs = exchange.get_pairs()
for pair in pairs:
    print(f"{pair['symbol']}: {pair['base_asset']}/{pair['quote_asset']}")

# 获取K线数据
import pandas as pd
klines = exchange.get_klines(
    symbol="BTCUSDT",
    interval="1h",
    limit=100,
)
print(klines.head())

# 获取实时行情
ticker = exchange.get_ticker("BTCUSDT")
print(f"最新价: {ticker['price']}")
print(f"24h涨跌: {ticker['price_change_percent']}%")
```

### 2. 创建加密货币策略

```python
from zquant.backtest.strategy import BaseStrategy
from zquant.backtest.crypto_context import CryptoContext

class SimpleMACryptoStrategy(BaseStrategy):
    """简单均线策略(加密货币)"""
    
    def initialize(self):
        """策略初始化"""
        self.short_period = 10
        self.long_period = 30
        self.position_size = 0.1  # 0.1 BTC
    
    def on_bar(self, context: CryptoContext, bar_data: dict):
        """K线回调"""
        symbol = "BTCUSDT"
        
        if symbol not in bar_data:
            return
        
        # 获取当前K线
        current_bar = bar_data[symbol]
        
        # TODO: 计算均线
        # short_ma = ...
        # long_ma = ...
        
        # 金叉买入
        # if short_ma > long_ma:
        #     context.order(symbol, self.position_size)
        
        # 死叉卖出
        # elif short_ma < long_ma:
        #     context.order(symbol, -self.position_size)
```

### 3. 运行加密货币回测

```python
from zquant.backtest.crypto_engine import CryptoBacktestEngine
from datetime import datetime, timedelta

# 配置回测
config = {
    "initial_capital": 10000.0,  # 初始资金10000 USDT
    "exchange": "binance",          # 交易所
    "symbols": ["BTCUSDT"],         # 交易对
    "interval": "1h",              # K线周期
    "start_time": datetime.now() - timedelta(days=30),
    "end_time": datetime.now(),
    "maker_fee": 0.001,           # Maker费率0.1%
    "taker_fee": 0.001,           # Taker费率0.1%
    "slippage_rate": 0.0005,      # 滑点率0.05%
}

# 创建并运行回测
engine = CryptoBacktestEngine(SimpleMACryptoStrategy, config)
results = engine.run()

print(f"总收益率: {results['total_return_pct']:.2f}%")
print(f"总交易次数: {results['total_trades']}")
```

## 关键差异对比

| 功能 | 股票 | 加密货币 |
|-----|------|---------|
| **交易时间** | T+1,交易日历 | T+0,24/7 |
| **交易机制** | 只能做多 | 可做多可做空 |
| **订单类型** | 市价单/限价单 | 市价/限价/止损/止盈 |
| **成本** | 佣金+印花税+滑点 | Maker费+Taker费+滑点 |
| **杠杆** | 融资融券(有限) | 合约杠杆(灵活) |
| **数据频率** | 日线/周线 | 秒级/分钟级/小时级 |
| **数据来源** | Tushare | Binance/OKX/Bybit |

## 注意事项

### 1. API限流

交易所API有严格的请求限制:
- 币安: 1200次/分钟
- OKX: 20次/秒
- Bybit: 120次/分钟

**解决方案**: 使用Redis缓存 + 请求队列

### 2. 数据量巨大

24/7高频交易产生海量数据:
- 1分钟K线: 1440条/天/交易对
- 100个交易对: 144,000条/天

**解决方案**:
- 采用时序数据库(InfluxDB)或分表策略
- 历史数据归档

### 3. 实时性要求

币圈对实时性要求极高:
- 使用WebSocket推送实时行情
- 使用消息队列处理订单
- 低延迟网络架构

### 4. 安全性

- API密钥加密存储
- 使用HTTPS连接
- 实盘操作需要二次确认

---

## 下一步计划

### P1 - 重要功能(待完成)

#### 1. 前端页面
- 加密货币行情页面
- K线图表展示
- 策略回测页面
- 持仓管理页面

#### 2. 调度任务
- 定时同步K线数据
- 定时更新交易对列表
- 定时获取实时行情

#### 3. WebSocket实时行情
- 实时价格推送
- 订单簿推送
- 成交推送

### P2 - 增强功能(待完成)

#### 1. 实盘交易
- 对接交易所交易API
- 订单管理
- 风控系统

#### 2. 高级功能
- 套利策略
- 网格交易
- 合约交易
- 期权交易
- 机器学习预测

#### 3. 数据分析
- 因子库
- 绩效分析
- 风险分析

---

**更新日期**: 2025-01-05
**维护者**: ZQuant Team
