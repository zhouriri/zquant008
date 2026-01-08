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
from typing import Optional

交易所工厂类
"""

from zquant.crypto.binance import BinanceExchange, BinanceFuturesExchange
from zquant.crypto.bybit import BybitExchange, BybitFuturesExchange
from zquant.crypto.exchange_base import ExchangeBase
from zquant.crypto.okx import OKXExchange, OKXFuturesExchange


class ExchangeFactory:
    """交易所工厂类 - 根据交易所名称创建对应的交易所客户端"""

    _exchanges = {
        # 现货
        "binance": BinanceExchange,
        "okx": OKXExchange,
        "bybit": BybitExchange,
        # 合约
        "binance_futures": BinanceFuturesExchange,
        "okx_futures": OKXFuturesExchange,
        "bybit_futures": BybitFuturesExchange,
    }

    @classmethod
    def create_exchange(
        cls,
        exchange_name: str,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
    ) -> ExchangeBase:
        """
        创建交易所客户端

        Args:
            exchange_name: 交易所名称(binanc/okx/bybit/binance_futures/okx_futures/bybit_futures)
            api_key: API Key
            api_secret: API Secret
            passphrase: API Passphrase(如OKX需要)

        Returns:
            交易所客户端实例

        Raises:
            ValueError: 不支持的交易所
        """
        exchange_class = cls._exchanges.get(exchange_name)
        
        if not exchange_class:
            supported = ", ".join(cls._exchanges.keys())
            raise ValueError(
                f"不支持的交易所: {exchange_name}. "
                f"支持的交易所: {supported}"
            )
        
        return exchange_class(api_key, api_secret, passphrase)

    @classmethod
    def register_exchange(cls, exchange_name: str, exchange_class: type[ExchangeBase]):
        """
        注册新的交易所

        Args:
            exchange_name: 交易所名称
            exchange_class: 交易所类
        """
        cls._exchanges[exchange_name] = exchange_class

    @classmethod
    def get_supported_exchanges(cls) -> list[str]:
        """获取所有支持的交易所列表"""
        return list(cls._exchanges.keys())
