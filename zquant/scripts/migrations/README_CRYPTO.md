# Cryptocurrency Migration for ZQuant

## 概述

此迁移脚本将ZQuant数据库结构扩展以支持加密货币数据存储。

## 新增表说明

### 1. 交易对表 (zq_data_crypto_pairs)
存储所有加密货币交易对信息。

### 2. K线数据表 (zq_data_crypto_klines_{interval})
按周期分表存储K线数据,支持多种周期。

### 3. 实时行情表 (zq_data_crypto_tickers)
存储实时行情数据。

### 4. 订单簿表 (zq_data_crypto_orderbook)
存储订单簿快照。

### 5. 资金费率表 (zq_data_crypto_funding_rates)
存储合约资金费率。

### 6. 自选交易对 (zq_app_crypto_favorites)
用户自选的交易对。

### 7. 用户持仓 (zq_app_crypto_positions)
用户持仓信息。

### 8. 交易记录 (zq_app_crypto_transactions)
用户交易历史记录。

### 9. 交易所配置 (zq_app_exchange_configs)
交易所API配置。

## 迁移步骤

### 1. 创建加密货币相关表

```bash
# 方式1: 使用Alembic迁移(推荐)
alembic revision -m "Add cryptocurrency support"
# 编辑生成的迁移文件,添加表创建语句
alembic upgrade head

# 方式2: 直接创建表
python zquant/scripts/create_crypto_tables.py
```

### 2. 初始化数据

```python
from zquant.data.crypto_sync import CryptoDataSyncService
from zquant.database import SessionLocal

# 创建数据库会话
db = SessionLocal()

# 创建同步服务
sync_service = CryptoDataSyncService(
    db_session=db,
    exchange_name="binance",
    api_key="your-api-key",
    api_secret="your-api-secret",
)

# 同步交易对
sync_service.sync_pairs(quote_asset="USDT", status="trading")

# 同步K线数据
sync_service.sync_klines(
    symbol="BTCUSDT",
    interval="1h",
    days_back=7,
)

# 关闭会话
db.close()
```

### 3. 验证表结构

```python
from zquant.utils.db_check import get_database_status

status = get_database_status()
print(f"已连接: {status['connected']}")
print(f"表存在: {status['tables_exist']}")
print(f"缺失的表: {status['missing_tables']}")
```

## 支持的K线周期

- 1m, 3m, 5m, 15m, 30m
- 1h, 2h, 4h, 6h, 8h, 12h
- 1d, 3d, 1w, 1M

## 注意事项

1. **API限流**: 交易所API有请求限制,请合理设置同步频率
2. **数据量**: K线数据量巨大,建议定期归档历史数据
3. **安全性**: API密钥需加密存储在生产环境
4. **性能**: 建议为常用字段添加索引

## 回滚

如需回滚加密货币功能:

```bash
# 使用Alembic回滚
alembic downgrade -1

# 或手动删除表
# DROP TABLE zq_data_crypto_pairs;
# DROP TABLE zq_data_crypto_klines_*;
# ... 等等
```

## 后续扩展

1. 支持更多交易所(Bybit, OKX)
2. 支持WebSocket实时行情
3. 支持合约交易
4. 支持期权交易
