# 加密货币模块快速开始指南

## 🚀 5分钟快速启动

### 第一步: 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
pip install -r requirements_crypto.txt

# 安装前端依赖
cd web
npm install
cd ..
```

### 第二步: 配置环境变量

在项目根目录创建 `.env` 文件:

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/zquant

# Redis配置
REDIS_URL=redis://localhost:6379/0

# Binance API密钥 (可选,用于私有接口)
BINANCE_API_KEY=your-api-key-here
BINANCE_API_SECRET=your-api-secret-here

# OKX API密钥 (可选)
OKX_API_KEY=your-api-key-here
OKX_API_SECRET=your-api-secret-here
OKX_PASSPHRASE=your-passphrase-here
```

### 第三步: 初始化数据库

```bash
# 方式1: 使用快速启动脚本(推荐)
python zquant/scripts/quick_start_crypto.py

# 方式2: 手动初始化
python zquant/scripts/create_crypto_tables.py
```

### 第四步: 启动服务

```bash
# 终端1: 启动后端API服务
python -m zquant.main

# 终端2: 启动前端开发服务器
cd web
npm run dev
```

### 第五步: 访问应用

打开浏览器访问: http://localhost:8000

然后点击左侧菜单中的 **加密货币(Crypto)**:

- **行情页面** - http://localhost:8000/crypto/market
- **K线图表** - http://localhost:8000/crypto/chart
- **数据同步** - http://localhost:8000/crypto/sync
- **策略回测** - http://localhost:8000/crypto/backtest

---

## 📊 功能概览

### 1. 实时行情

查看热门加密货币的实时价格、涨跌幅、交易量等信息。

### 2. K线图表

查看任意交易对的K线图,支持多种周期(1m, 5m, 15m, 30m, 1h, 4h, 1d)。

### 3. 数据同步

手动同步交易对列表和K线数据,或配置定时任务自动同步。

### 4. 策略回测

内置5种策略,可配置参数进行回测:
- 均线策略
- 突破策略
- 网格交易
- RSI策略
- 趋势跟踪

---

## 🔧 常用命令

### 数据库操作

```bash
# 创建所有加密货币表
python zquant/scripts/create_crypto_tables.py

# 测试回测
python zquant/scripts/test_crypto_backtest.py
```

### 数据同步

```bash
# 快速启动(自动同步基础数据)
python zquant/scripts/quick_start_crypto.py

# 手动同步K线数据
python -c "
import asyncio
from zquant.data.crypto_sync import CryptoDataSync

async def sync():
    sync = CryptoDataSync()
    await sync.sync_klines('BTCUSDT', '1d', force=True)

asyncio.run(sync())
"
```

### 调度任务

```bash
# 初始化加密货币调度任务
python zquant/scripts/init_crypto_scheduler.py

# 查看任务状态(需要登录系统)
# 访问: http://localhost:8000/scheduler
```

### 数据分析

```bash
# 分析工具
python zquant/scripts/crypto_analysis_tools.py

# 实时监控
python zquant/scripts/crypto_monitor.py
```

---

## 📚 API接口

所有加密货币API都前缀为 `/api/v1`

### 获取交易对列表

```bash
curl http://localhost:8000/api/v1/crypto/pairs
```

### 获取K线数据

```bash
# 获取BTC 1天K线
curl "http://localhost:8000/api/v1/crypto/klines?symbol=BTCUSDT&interval=1d&limit=100"
```

### 获取实时行情

```bash
curl http://localhost:8000/api/v1/crypto/ticker/BTCUSDT
```

### 同步数据

```bash
# 同步交易对
curl -X POST http://localhost:8000/api/v1/crypto/sync/pairs

# 同步K线数据
curl -X POST "http://localhost:8000/api/v1/crypto/sync/klines?symbol=BTCUSDT&interval=1d"
```

更多API文档请访问: http://localhost:8000/docs

---

## 💡 使用示例

### 示例1: 运行回测

```python
from zquant.backtest.crypto_engine import CryptoBacktestEngine
from zquant.strategies.crypto_strategies import MovingAverageCryptoStrategy

# 创建策略
strategy = MovingAverageCryptoStrategy(
    symbol="BTCUSDT",
    interval="1d",
    short_period=7,
    long_period=25,
)

# 运行回测
engine = CryptoBacktestEngine()
result = engine.run(
    strategy=strategy,
    start_date="2024-01-01",
    end_date="2024-12-31",
    initial_capital=100000,
)

# 打印结果
print(f"总收益率: {result['total_return']:.2%}")
print(f"年化收益: {result['annual_return']:.2%}")
print(f"夏普比率: {result['sharpe_ratio']:.2f}")
```

### 示例2: 获取实时数据

```python
import asyncio
from zquant.crypto.exchange_factory import ExchangeFactory

async def get_price():
    binance = ExchangeFactory.create_exchange("binance")
    ticker = await binance.get_ticker("BTCUSDT")
    print(f"BTC价格: ${ticker['price']}")

asyncio.run(get_price())
```

### 示例3: 创建自定义策略

```python
from zquant.backtest.crypto_context import CryptoContext
from zquant.strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, context: CryptoContext):
        super().__init__(context)
        self.name = "My Custom Strategy"
    
    def on_bar(self):
        # 你的策略逻辑
        current_price = self.context.get_current_price()
        sma_20 = self.context.get_sma(20)
        
        if current_price > sma_20:
            self.context.buy(100)  # 买入100单位
        else:
            self.context.sell(100)  # 卖出100单位
```

---

## 🎯 下一步

- 查看 [CRYPTO_FINAL_SUMMARY.md](../CRYPTO_FINAL_SUMMARY.md) 了解完整功能
- 查看 [zquant/crypto/README.md](../zquant/crypto/README.md) 了解开发文档
- 配置定时任务自动同步数据
- 开发自定义策略

---

## ❓ 常见问题

### Q: 数据同步失败怎么办?

A: 检查以下几点:
1. 网络连接是否正常
2. API密钥是否正确(需要时)
3. 数据库是否连接成功
4. 查看日志获取详细错误信息

### Q: 回测结果不准确?

A: 可能的原因:
1. K线数据不完整
2. 回测参数设置错误
3. 策略逻辑有问题
4. 费率设置不正确

### Q: 如何添加新交易所?

A: 参考 `zquant/crypto/exchange_base.py` 创建新的交易所类,继承 `ExchangeBase`。

### Q: 前端页面显示空白?

A: 检查:
1. 后端API是否正常运行
2. 浏览器控制台是否有错误
3. 网络请求是否成功

---

## 📞 获取帮助

- **Issues**: https://github.com/yoyoung/zquant/issues
- **文档**: https://github.com/yoyoung/zquant/blob/main/README.md
- **邮箱**: kevin@vip.qq.com
- **微信**: zquant2025

---

**祝你使用愉快! 🚀**
