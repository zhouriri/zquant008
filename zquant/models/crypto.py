# Copyright 2025 ZQuant Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
加密货币相关数据库模型
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import DOUBLE as Double
from sqlalchemy.orm import relationship

from zquant.database import AuditMixin, Base

# 币种状态常量
TRADING_STATUS_TRADING = "trading"
TRADING_STATUS_BREAK = "break"
TRADING_STATUS_DELISTED = "delisted"

# 订单类型常量
ORDER_TYPE_MARKET = "market"
ORDER_TYPE_LIMIT = "limit"
ORDER_TYPE_STOP_LIMIT = "stop_limit"
ORDER_TYPE_STOP_MARKET = "stop_market"

# 交易方向常量
ORDER_SIDE_BUY = "buy"
ORDER_SIDE_SELL = "sell"


class CryptoPair(Base, AuditMixin):
    """交易对表"""

    __tablename__ = "zq_data_crypto_pairs"
    __cnname__ = "交易对"
    __docs__ = "加密货币交易对基本信息"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True, comment="交易对符号,如BTCUSDT")
    base_asset = Column(String(10), nullable=False, index=True, comment="基础资产,如BTC")
    quote_asset = Column(String(10), nullable=False, index=True, comment="计价资产,如USDT")
    exchange = Column(String(20), nullable=False, index=True, comment="交易所,如binance、okx、bybit")
    status = Column(String(20), nullable=False, default=TRADING_STATUS_TRADING, comment="交易状态:trading/break/delisted")
    contract_type = Column(String(20), nullable=True, comment="合约类型:spot/futures/perpetual")
    price_precision = Column(Integer, nullable=False, default=2, comment="价格精度")
    quantity_precision = Column(Integer, nullable=False, default=8, comment="数量精度")
    min_order_amount = Column(Float, nullable=False, default=0.0, comment="最小下单金额")
    min_order_quantity = Column(Float, nullable=False, default=0.0, comment="最小下单数量")

    __table_args__ = (
        Index("idx_exchange_symbol", "exchange", "symbol"),
        Index("idx_base_quote", "base_asset", "quote_asset"),
    )


class CryptoKline(Base, AuditMixin):
    """K线数据表(分表)"""

    __tablename__ = "zq_data_crypto_klines"
    __cnname__ = "K线数据"
    __docs__ = "加密货币K线数据,按时间周期分表存储"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="交易对符号")
    interval = Column(String(10), nullable=False, index=True, comment="K线周期:1m/5m/15m/1h/4h/1d/1w")
    timestamp = Column(DateTime, nullable=False, index=True, comment="时间戳")
    open = Column(Double, nullable=False, comment="开盘价")
    high = Column(Double, nullable=False, comment="最高价")
    low = Column(Double, nullable=False, comment="最低价")
    close = Column(Double, nullable=False, comment="收盘价")
    volume = Column(Double, nullable=False, comment="成交量")
    quote_volume = Column(Double, nullable=False, comment="成交额")
    trades_count = Column(Integer, nullable=True, comment="成交笔数")
    taker_buy_base = Column(Double, nullable=True, comment="主动买入量")
    taker_buy_quote = Column(Double, nullable=True, comment="主动买入额")

    __table_args__ = (
        Index("idx_symbol_interval_time", "symbol", "interval", "timestamp"),
        Index("idx_timestamp", "timestamp"),
    )


class CryptoTicker(Base, AuditMixin):
    """实时行情表"""

    __tablename__ = "zq_data_crypto_tickers"
    __cnname__ = "实时行情"
    __docs__ = "加密货币实时行情数据"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True, comment="交易对符号")
    exchange = Column(String(20), nullable=False, index=True, comment="交易所")
    price = Column(Double, nullable=False, comment="最新价")
    price_change = Column(Double, nullable=False, default=0.0, comment="价格变化")
    price_change_percent = Column(Float, nullable=False, default=0.0, comment="价格变化百分比")
    high_24h = Column(Double, nullable=False, comment="24小时最高价")
    low_24h = Column(Double, nullable=False, comment="24小时最低价")
    volume_24h = Column(Double, nullable=False, comment="24小时成交量")
    quote_volume_24h = Column(Double, nullable=False, comment="24小时成交额")
    open_24h = Column(Double, nullable=False, comment="24小时开盘价")

    __table_args__ = (
        Index("idx_exchange_symbol", "exchange", "symbol"),
    )


class CryptoOrderBook(Base, AuditMixin):
    """订单簿快照表"""

    __tablename__ = "zq_data_crypto_orderbook"
    __cnname__ = "订单簿"
    __docs__ = "加密货币订单簿快照数据"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="交易对符号")
    exchange = Column(String(20), nullable=False, index=True, comment="交易所")
    timestamp = Column(DateTime, nullable=False, index=True, comment="时间戳")
    bids_json = Column(Text, nullable=False, comment="买单列表JSON:[[price,quantity],...]")
    asks_json = Column(Text, nullable=False, comment="卖单列表JSON:[[price,quantity],...]")

    __table_args__ = (
        Index("idx_symbol_time", "symbol", "timestamp"),
    )


class CryptoFundingRate(Base, AuditMixin):
    """资金费率表(合约)"""

    __tablename__ = "zq_data_crypto_funding_rates"
    __cnname__ = "资金费率"
    __docs__ = "永续合约资金费率数据"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="交易对符号")
    exchange = Column(String(20), nullable=False, index=True, comment="交易所")
    funding_rate = Column(Float, nullable=False, comment="资金费率")
    funding_time = Column(DateTime, nullable=False, index=True, comment="资金费率时间")
    estimated_rate = Column(Float, nullable=True, comment="预估资金费率")
    mark_price = Column(Double, nullable=False, comment="标记价格")
    index_price = Column(Double, nullable=False, comment="指数价格")

    __table_args__ = (
        Index("idx_symbol_time", "symbol", "funding_time"),
    )


class CryptoFavorite(Base, AuditMixin):
    """用户自选交易对表"""

    __tablename__ = "zq_app_crypto_favorites"
    __cnname__ = "自选交易对"
    __docs__ = "用户关注的加密货币交易对"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    symbol = Column(String(20), nullable=False, index=True, comment="交易对符号")
    exchange = Column(String(20), nullable=False, comment="交易所")
    reason = Column(Text, nullable=True, comment="关注理由")
    tags = Column(String(200), nullable=True, comment="标签,逗号分隔")

    __table_args__ = (
        Index("idx_user_symbol", "user_id", "symbol"),
    )


class CryptoPosition(Base, AuditMixin):
    """用户持仓表"""

    __tablename__ = "zq_app_crypto_positions"
    __cnname__ = "持仓记录"
    __docs__ = "用户加密货币持仓记录"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    symbol = Column(String(20), nullable=False, index=True, comment="交易对符号")
    exchange = Column(String(20), nullable=False, comment="交易所")
    position_type = Column(String(20), nullable=False, comment="持仓类型:spot/long/short")
    quantity = Column(Double, nullable=False, comment="持仓数量")
    entry_price = Column(Double, nullable=False, comment="开仓价格")
    leverage = Column(Float, nullable=True, default=1.0, comment="杠杆倍数")
    unrealized_pnl = Column(Float, nullable=False, default=0.0, comment="未实现盈亏")
    margin_used = Column(Float, nullable=False, default=0.0, comment="占用保证金")
    entry_time = Column(DateTime, nullable=False, comment="开仓时间")

    __table_args__ = (
        Index("idx_user_symbol", "user_id", "symbol"),
    )


class CryptoTransaction(Base, AuditMixin):
    """交易记录表"""

    __tablename__ = "zq_app_crypto_transactions"
    __cnname__ = "交易记录"
    __docs__ = "用户加密货币交易记录"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    symbol = Column(String(20), nullable=False, index=True, comment="交易对符号")
    exchange = Column(String(20), nullable=False, comment="交易所")
    order_type = Column(String(20), nullable=False, comment="订单类型:market/limit/...")
    order_side = Column(String(20), nullable=False, comment="交易方向:buy/sell")
    quantity = Column(Double, nullable=False, comment="成交数量")
    price = Column(Double, nullable=False, comment="成交价格")
    value = Column(Double, nullable=False, comment="成交金额")
    fee = Column(Double, nullable=False, default=0.0, comment="手续费")
    is_maker = Column(Boolean, nullable=False, default=False, comment="是否为Maker订单")
    transaction_time = Column(DateTime, nullable=False, comment="交易时间")

    __table_args__ = (
        Index("idx_user_time", "user_id", "transaction_time"),
        Index("idx_symbol_time", "symbol", "transaction_time"),
    )


class ExchangeConfig(Base, AuditMixin):
    """交易所配置表"""

    __tablename__ = "zq_app_exchange_configs"
    __cnname__ = "交易所配置"
    __docs__ = "交易所API配置信息"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    exchange = Column(String(20), nullable=False, unique=True, comment="交易所名称")
    api_key = Column(String(200), nullable=False, comment="API Key")
    api_secret = Column(String(200), nullable=False, comment="API Secret")
    passphrase = Column(String(100), nullable=True, comment="API Passphrase(如OKX)")
    is_testnet = Column(Boolean, nullable=False, default=False, comment="是否为测试网络")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")

    __table_args__ = (
        Index("idx_user_exchange", "user_id", "exchange"),
    )


def get_kline_table_name(symbol: str, interval: str) -> str:
    """获取K线数据表名(按交易对和周期分表)"""
    # 转换特殊字符,如BTCUSDT -> BTCUSDT
    return f"zq_data_crypto_klines_{symbol}_{interval}"


def create_kline_table_class(symbol: str, interval: str):
    """动态创建K线表模型类"""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def _create_class():
        table_name = get_kline_table_name(symbol, interval)
        
        class CryptoKlinePartition(Base, AuditMixin):
            """K线数据分表"""
            __tablename__ = table_name
            __cnname__ = f"K线数据({symbol}-{interval})"
            
            id = Column(Integer, primary_key=True, index=True, autoincrement=True)
            timestamp = Column(DateTime, nullable=False, index=True, comment="时间戳")
            open = Column(Double, nullable=False, comment="开盘价")
            high = Column(Double, nullable=False, comment="最高价")
            low = Column(Double, nullable=False, comment="最低价")
            close = Column(Double, nullable=False, comment="收盘价")
            volume = Column(Double, nullable=False, comment="成交量")
            quote_volume = Column(Double, nullable=False, comment="成交额")
            trades_count = Column(Integer, nullable=True, comment="成交笔数")
            taker_buy_base = Column(Double, nullable=True, comment="主动买入量")
            taker_buy_quote = Column(Double, nullable=True, comment="主动买入额")
            
            __table_args__ = (
                Index("idx_timestamp", "timestamp"),
            )
        
        return CryptoKlinePartition
    
    return _create_class()


__all__ = [
    "CryptoPair",
    "CryptoKline",
    "CryptoTicker",
    "CryptoOrderBook",
    "CryptoFundingRate",
    "CryptoFavorite",
    "CryptoPosition",
    "CryptoTransaction",
    "ExchangeConfig",
    "create_kline_table_class",
    "get_kline_table_name",
]
