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
交易所数据源基类
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import pandas as pd


class ExchangeBase(ABC):
    """交易所数据源基类"""

    def __init__(self, api_key: str, api_secret: str, passphrase: str | None = None):
        """
        初始化交易所客户端

        Args:
            api_key: API Key
            api_secret: API Secret
            passphrase: API Passphrase(如OKX需要)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase

    @abstractmethod
    def get_exchange_name(self) -> str:
        """获取交易所名称"""
        pass

    @abstractmethod
    def get_pairs(self) -> list[dict[str, Any]]:
        """
        获取所有交易对列表

        Returns:
            交易对列表,每个交易对包含:
            - symbol: 交易对符号(BTCUSDT)
            - base_asset: 基础资产(BTC)
            - quote_asset: 计价资产(USDT)
            - status: 交易状态
            - price_precision: 价格精度
            - quantity_precision: 数量精度
        """
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> dict[str, Any]:
        """
        获取单个交易对实时行情

        Args:
            symbol: 交易对符号(BTCUSDT)

        Returns:
            行情数据字典:
            - price: 最新价
            - price_change: 价格变化
            - price_change_percent: 价格变化百分比
            - high_24h: 24小时最高价
            - low_24h: 24小时最低价
            - volume_24h: 24小时成交量
            - quote_volume_24h: 24小时成交额
        """
        pass

    @abstractmethod
    def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        获取K线数据

        Args:
            symbol: 交易对符号(BTCUSDT)
            interval: K线周期(1m/5m/15m/1h/4h/1d/1w)
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回条数限制

        Returns:
            K线数据DataFrame,包含列:
            - timestamp: 时间戳
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - quote_volume: 成交额
        """
        pass

    @abstractmethod
    def get_orderbook(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        """
        获取订单簿

        Args:
            symbol: 交易对符号(BTCUSDT)
            limit: 深度(默认20档)

        Returns:
            订单簿数据:
            - timestamp: 时间戳
            - bids: 买单列表[[price, quantity], ...]
            - asks: 卖单列表[[price, quantity], ...]
        """
        pass

    @abstractmethod
    def get_funding_rate(self, symbol: str) -> dict[str, Any]:
        """
        获取资金费率(永续合约)

        Args:
            symbol: 交易对符号(BTCUSDT)

        Returns:
            资金费率数据:
            - funding_rate: 资金费率
            - funding_time: 资金费率时间
            - mark_price: 标记价格
            - index_price: 指数价格
        """
        pass

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
    ) -> pd.DataFrame:
        """
        获取历史K线数据(分页获取)

        Args:
            symbol: 交易对符号
            interval: K线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            完整的K线数据DataFrame
        """
        all_data = []
        current_start = start_time
        
        while current_start < end_time:
            # 获取一批数据
            batch_data = self.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=current_start,
                end_time=end_time,
                limit=1000,
            )
            
            if batch_data.empty:
                break
            
            all_data.append(batch_data)
            
            # 更新起始时间为最后一条数据的时间
            last_timestamp = batch_data.iloc[-1]["timestamp"]
            current_start = last_timestamp + timedelta(minutes=1)
            
            # 避免无限循环
            if len(batch_data) < 1000:
                break
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

    def standardize_kline_data(self, raw_data: list[dict[str, Any]], interval: str) -> pd.DataFrame:
        """
        标准化K线数据为统一格式

        Args:
            raw_data: 原始K线数据
            interval: K线周期

        Returns:
            标准化的DataFrame
        """
        # 子类可以根据需要重写此方法
        pass
