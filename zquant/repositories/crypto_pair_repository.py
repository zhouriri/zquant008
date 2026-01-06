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
加密货币交易对Repository

统一交易对数据访问，提供批量查询和缓存优化
"""

from typing import List, Optional
from loguru import logger
from sqlalchemy.orm import Session

from zquant.models.crypto import CryptoPair
from zquant.utils.cache import get_cache


class CryptoPairRepository:
    """加密货币交易对Repository"""

    def __init__(self, db: Session):
        """
        初始化Repository

        Args:
            db: 数据库会话
        """
        self.db = db
        self.cache = get_cache()
        self._cache_prefix = "crypto:pair:"

    def get_by_symbol(self, symbol: str) -> Optional[CryptoPair]:
        """
        根据交易对符号获取

        Args:
            symbol: 交易对符号

        Returns:
            CryptoPair对象或None
        """
        cache_key = f"{self._cache_prefix}{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        pair = self.db.query(CryptoPair).filter(
            CryptoPair.symbol == symbol
        ).first()

        if pair:
            self.cache.set(cache_key, pair, timeout=3600)
        return pair

    def get_all(self, skip: int = 0, limit: int = 100) -> List[CryptoPair]:
        """
        获取所有交易对

        Args:
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            交易对列表
        """
        cache_key = f"{self._cache_prefix}all:{skip}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        pairs = self.db.query(CryptoPair).order_by(
            CryptoPair.volume_24h.desc()
        ).offset(skip).limit(limit).all()

        self.cache.set(cache_key, pairs, timeout=300)
        return pairs

    def get_by_exchange(self, exchange: str, skip: int = 0, limit: int = 100) -> List[CryptoPair]:
        """
        根据交易所获取交易对

        Args:
            exchange: 交易所名称
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            交易对列表
        """
        return self.db.query(CryptoPair).filter(
            CryptoPair.exchange == exchange
        ).order_by(CryptoPair.volume_24h.desc()).offset(skip).limit(limit).all()

    def get_top_by_volume(self, limit: int = 10) -> List[CryptoPair]:
        """
        获取交易量最大的交易对

        Args:
            limit: 返回数量限制

        Returns:
            交易对列表
        """
        cache_key = f"{self._cache_prefix}top_volume:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        pairs = self.db.query(CryptoPair).order_by(
            CryptoPair.volume_24h.desc()
        ).limit(limit).all()

        self.cache.set(cache_key, pairs, timeout=600)
        return pairs

    def get_by_symbols(self, symbols: List[str]) -> List[CryptoPair]:
        """
        批量获取交易对(替代N+1查询)

        Args:
            symbols: 交易对符号列表

        Returns:
            交易对列表
        """
        if not symbols:
            return []

        # 批量查询
        pairs = self.db.query(CryptoPair).filter(
            CryptoPair.symbol.in_(symbols)
        ).all()

        # 建立映射
        pair_map = {pair.symbol: pair for pair in pairs}

        # 返回按输入顺序排序的结果
        result = []
        for symbol in symbols:
            if symbol in pair_map:
                result.append(pair_map[symbol])

        return result

    def create(self, pair: CryptoPair) -> CryptoPair:
        """
        创建交易对

        Args:
            pair: CryptoPair对象

        Returns:
            创建的CryptoPair对象
        """
        self.db.add(pair)
        self.db.commit()
        self.db.refresh(pair)

        # 清除缓存
        self._clear_all_cache()

        return pair

    def create_batch(self, pairs: List[CryptoPair]) -> List[CryptoPair]:
        """
        批量创建交易对

        Args:
            pairs: CryptoPair对象列表

        Returns:
            创建的CryptoPair对象列表
        """
        self.db.add_all(pairs)
        self.db.commit()

        # 清除缓存
        self._clear_all_cache()

        return pairs

    def update(self, pair: CryptoPair) -> CryptoPair:
        """
        更新交易对

        Args:
            pair: CryptoPair对象

        Returns:
            更新后的CryptoPair对象
        """
        self.db.merge(pair)
        self.db.commit()

        # 清除缓存
        cache_key = f"{self._cache_prefix}{pair.symbol}"
        self.cache.delete(cache_key)
        self._clear_all_cache()

        return pair

    def delete(self, symbol: str) -> bool:
        """
        删除交易对

        Args:
            symbol: 交易对符号

        Returns:
            是否删除成功
        """
        pair = self.get_by_symbol(symbol)
        if pair:
            self.db.delete(pair)
            self.db.commit()

            # 清除缓存
            cache_key = f"{self._cache_prefix}{symbol}"
            self.cache.delete(cache_key)
            self._clear_all_cache()

            return True
        return False

    def count(self) -> int:
        """
        统计交易对数量

        Returns:
            交易对数量
        """
        return self.db.query(CryptoPair).count()

    def _clear_all_cache(self):
        """清除所有交易对缓存"""
        # 在实际项目中,可以使用Redis的模式匹配删除
        # 这里简化处理,只清除特定的缓存键
        pass
