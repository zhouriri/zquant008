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
加密货币K线Repository

统一K线数据访问,提供批量查询和缓存优化
"""

from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger
from sqlalchemy.orm import Session

from zquant.models.crypto import get_kline_table_name, create_kline_table_class
from zquant.utils.cache import get_cache


class CryptoKlineRepository:
    """加密货币K线Repository"""

    def __init__(self, db: Session):
        """
        初始化Repository

        Args:
            db: 数据库会话
        """
        self.db = db
        self.cache = get_cache()
        self._cache_prefix = "crypto:kline:"

    def _get_table(self, interval: str):
        """
        获取K线表类

        Args:
            interval: K线周期

        Returns:
            K线表类
        """
        table_name = get_kline_table_name(interval)
        return create_kline_table_class(table_name)

    def get_latest(self, symbol: str, interval: str, limit: int = 100) -> List[dict]:
        """
        获取最新K线数据

        Args:
            symbol: 交易对符号
            interval: K线周期
            limit: 返回数量限制

        Returns:
            K线数据列表
        """
        table = self._get_table(interval)
        cache_key = f"{self._cache_prefix}{symbol}:{interval}:latest:{limit}"

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        klines = self.db.query(table).filter(
            table.symbol == symbol
        ).order_by(table.open_time.desc()).limit(limit).all()

        # 转换为字典列表
        result = [
            {
                "timestamp": k.open_time,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
            }
            for k in klines
        ]

        self.cache.set(cache_key, result, timeout=60)
        return result

    def get_by_time_range(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[dict]:
        """
        获取指定时间范围的K线数据

        Args:
            symbol: 交易对符号
            interval: K线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            K线数据列表
        """
        table = self._get_table(interval)

        klines = self.db.query(table).filter(
            table.symbol == symbol,
            table.open_time >= start_time,
            table.open_time <= end_time
        ).order_by(table.open_time.asc()).all()

        return [
            {
                "timestamp": k.open_time,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
            }
            for k in klines
        ]

    def create_batch(self, klines: List[dict], interval: str) -> int:
        """
        批量创建K线数据

        Args:
            klines: K线数据列表
            interval: K线周期

        Returns:
            创建的K线数量
        """
        if not klines:
            return 0

        table = self._get_table(interval)
        count = 0

        for kline_data in klines:
            # 检查是否已存在
            existing = self.db.query(table).filter(
                table.symbol == kline_data["symbol"],
                table.open_time == kline_data["open_time"]
            ).first()

            if existing:
                # 更新
                existing.open = kline_data["open"]
                existing.high = kline_data["high"]
                existing.low = kline_data["low"]
                existing.close = kline_data["close"]
                existing.volume = kline_data["volume"]
                existing.quote_volume = kline_data.get("quote_volume", 0)
                existing.close_time = kline_data.get("close_time", kline_data["open_time"])
            else:
                # 新增
                kline_obj = table(
                    symbol=kline_data["symbol"],
                    open_time=kline_data["open_time"],
                    open=kline_data["open"],
                    high=kline_data["high"],
                    low=kline_data["low"],
                    close=kline_data["close"],
                    volume=kline_data["volume"],
                    quote_volume=kline_data.get("quote_volume", 0),
                    close_time=kline_data.get("close_time", kline_data["open_time"]),
                    trades=kline_data.get("trades", 0),
                )
                self.db.add(kline_obj)

            count += 1

        self.db.commit()

        # 清除缓存
        symbol = klines[0]["symbol"]
        self._clear_cache(symbol, interval)

        return count

    def get_latest_timestamp(self, symbol: str, interval: str) -> Optional[datetime]:
        """
        获取最新的K线时间戳

        Args:
            symbol: 交易对符号
            interval: K线周期

        Returns:
            最新时间戳或None
        """
        table = self._get_table(interval)

        kline = self.db.query(table).filter(
            table.symbol == symbol
        ).order_by(table.open_time.desc()).first()

        return kline.open_time if kline else None

    def count(self, symbol: str, interval: str) -> int:
        """
        统计K线数量

        Args:
            symbol: 交易对符号
            interval: K线周期

        Returns:
            K线数量
        """
        table = self._get_table(interval)
        return self.db.query(table).filter(
            table.symbol == symbol
        ).count()

    def delete_by_time_range(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """
        删除指定时间范围的K线数据

        Args:
            symbol: 交易对符号
            interval: K线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            删除的K线数量
        """
        table = self._get_table(interval)

        deleted = self.db.query(table).filter(
            table.symbol == symbol,
            table.open_time >= start_time,
            table.open_time <= end_time
        ).delete()

        self.db.commit()

        # 清除缓存
        self._clear_cache(symbol, interval)

        return deleted

    def _clear_cache(self, symbol: str, interval: str):
        """清除指定K线缓存"""
        pattern = f"{self._cache_prefix}{symbol}:{interval}:*"
        # 在实际项目中,可以使用Redis的模式匹配删除
        # 这里简化处理
        self.cache.delete(f"{self._cache_prefix}{symbol}:{interval}:latest:100")
