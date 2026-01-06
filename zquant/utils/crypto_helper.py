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
#
# Author: kevin
# Contact:
#     - Email: kevin@vip.qq.com
#     - Wechat: zquant2025
#     - Issues: https://github.com/yoyoung/zquant/issues
#     - Documentation: https://github.com/yoyoung/zquant/blob/main/README.md
#     - Repository: https://github.com/yoyoung/zquant

"""
加密货币工具类
"""

from typing import Tuple, Optional


class CryptoHelper:
    """加密货币工具类"""

    # 周期到秒数的映射
    INTERVAL_SECONDS = {
        '1m': 60,
        '3m': 180,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '4h': 14400,
        '6h': 21600,
        '8h': 28800,
        '12h': 43200,
        '1d': 86400,
        '3d': 259200,
        '1w': 604800,
        '1M': 2592000,
    }

    # 标准周期格式
    STANDARD_INTERVALS = {
        '1m', '3m', '5m', '15m', '30m',
        '1h', '2h', '4h', '6h', '8h', '12h',
        '1d', '3d', '1w', '1M'
    }

    @staticmethod
    def symbol_to_base_quote(symbol: str) -> Tuple[str, str]:
        """
        将交易对符号拆分为base和quote资产

        Examples:
            BTCUSDT -> (BTC, USDT)
            ETH/BTC -> (ETH, BTC)
            BNB-USD -> (BNB, USD)

        Args:
            symbol: 交易对符号

        Returns:
            (base_asset, quote_asset)
        """
        # 处理不同的分隔符
        if '/' in symbol:
            parts = symbol.split('/')
        elif '-' in symbol:
            parts = symbol.split('-')
        else:
            # 默认处理: 找到常见的quote资产
            common_quotes = ['USDT', 'USDC', 'BUSD', 'USD', 'BTC', 'ETH']
            for quote in common_quotes:
                if symbol.endswith(quote):
                    base = symbol[:-len(quote)]
                    return (base, quote)
            # 如果找不到,使用启发式方法
            # 假设最后3-5个字符是quote
            if len(symbol) > 5:
                base = symbol[:-4]
                quote = symbol[-4:]
                return (base, quote)
            else:
                return (symbol, '')

        return (parts[0], parts[1] if len(parts) > 1 else '')

    @staticmethod
    def get_interval_seconds(interval: str) -> int:
        """
        获取周期对应的秒数

        Args:
            interval: K线周期(如 1m, 5m, 1h, 1d)

        Returns:
            秒数
        """
        normalized = CryptoHelper.normalize_interval(interval)
        return CryptoHelper.INTERVAL_SECONDS.get(normalized, 86400)  # 默认1天

    @staticmethod
    def normalize_interval(interval: str) -> str:
        """
        标准化周期格式

        将不同的周期格式统一为标准格式

        Examples:
            1min -> 1m
            5mins -> 5m
            1hour -> 1h
            1day -> 1d
            1w -> 1w

        Args:
            interval: 周期字符串

        Returns:
            标准化的周期字符串
        """
        # 小写处理
        interval = interval.lower()

        # 映射表
        mappings = {
            '1min': '1m', '3min': '3m', '5min': '5m',
            '15min': '15m', '30min': '30m',
            '1hour': '1h', '2hour': '2h', '4hour': '4h',
            '6hour': '6h', '8hour': '8h', '12hour': '12h',
            '1day': '1d', '3day': '3d',
            '1week': '1w', '1month': '1M',
            '1m': '1m', '3m': '3m', '5m': '5m',
            '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '4h': '4h',
            '6h': '6h', '8h': '8h', '12h': '12h',
            '1d': '1d', '3d': '3d',
            '1w': '1w', '1M': '1M',
        }

        return mappings.get(interval, '1d')  # 默认1天

    @staticmethod
    def is_valid_interval(interval: str) -> bool:
        """
        检查周期是否有效

        Args:
            interval: 周期字符串

        Returns:
            是否有效
        """
        normalized = CryptoHelper.normalize_interval(interval)
        return normalized in CryptoHelper.STANDARD_INTERVALS

    @staticmethod
    def format_price(price: float, decimals: int = 2) -> str:
        """
        格式化价格

        Args:
            price: 价格
            decimals: 小数位数

        Returns:
            格式化后的价格字符串
        """
        if price is None:
            return 'N/A'

        # 根据价格大小自动调整小数位数
        if decimals == 0:
            if price >= 1000:
                decimals = 2
            elif price >= 1:
                decimals = 4
            else:
                decimals = 8

        return f"{price:.{decimals}f}"

    @staticmethod
    def format_volume(volume: float) -> str:
        """
        格式化交易量

        Args:
            volume: 交易量

        Returns:
            格式化后的交易量字符串
        """
        if volume is None:
            return 'N/A'

        if volume >= 1e9:
            return f"{volume / 1e9:.2f}B"
        elif volume >= 1e6:
            return f"{volume / 1e6:.2f}M"
        elif volume >= 1e3:
            return f"{volume / 1e3:.2f}K"
        else:
            return f"{volume:.2f}"

    @staticmethod
    def calculate_change_percent(current: float, previous: float) -> float:
        """
        计算涨跌幅百分比

        Args:
            current: 当前价格
            previous: 前一价格

        Returns:
            涨跌幅百分比
        """
        if previous == 0:
            return 0.0
        return (current - previous) / previous * 100

    @staticmethod
    def parse_symbol_from_ticker(ticker: str) -> Tuple[str, str]:
        """
        从ticker字符串解析交易对

        Args:
            ticker: ticker字符串

        Returns:
            (base_asset, quote_asset)
        """
        return CryptoHelper.symbol_to_base_quote(ticker)

    @staticmethod
    def create_symbol(base: str, quote: str, separator: str = '') -> str:
        """
        创建交易对符号

        Args:
            base: 基础资产
            quote: 计价资产
            separator: 分隔符

        Returns:
            交易对符号
        """
        return f"{base}{separator}{quote}"

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        验证交易对符号格式

        Args:
            symbol: 交易对符号

        Returns:
            是否有效
        """
        if not symbol or len(symbol) < 6:
            return False

        base, quote = CryptoHelper.symbol_to_base_quote(symbol)

        if not base or not quote:
            return False

        # 检查是否包含非字母字符(允许字母和常见分隔符)
        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ/-')
        return all(c in allowed_chars for c in symbol.upper())
