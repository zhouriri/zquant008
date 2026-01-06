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
加密货币数据同步服务
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import time

import pandas as pd
from loguru import logger
from sqlalchemy.orm import Session

from zquant.crypto import ExchangeFactory
from zquant.models.crypto import (
    CryptoPair,
    create_kline_table_class,
    get_kline_table_name,
)


class CryptoDataSyncService:
    """加密货币数据同步服务"""

    # 支持的K线周期
    SUPPORTED_INTERVALS = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]

    def __init__(self, db_session: Session, exchange_name: str = "binance", **exchange_config):
        """
        初始化同步服务

        Args:
            db_session: 数据库会话
            exchange_name: 交易所名称
            exchange_config: 交易所配置(api_key, api_secret, passphrase)
        """
        self.db = db_session
        self.exchange_name = exchange_name
        
        # 创建交易所客户端
        self.exchange = ExchangeFactory.create_exchange(exchange_name, **exchange_config)

    def sync_pairs(self, quote_asset: str = "USDT", status: str = "trading") -> int:
        """
        同步交易对列表

        Args:
            quote_asset: 计价资产(如USDT)
            status: 交易状态(trading/break)

        Returns:
            新增/更新的交易对数量
        """
        logger.info(f"开始同步交易对列表: {self.exchange_name}, quote={quote_asset}")
        
        try:
            # 获取交易对列表
            pairs_data = self.exchange.get_pairs(quote_asset=quote_asset, status=status)
            
            updated_count = 0
            for pair_info in pairs_data:
                symbol = pair_info["symbol"]
                
                # 查询是否已存在
                existing = self.db.query(CryptoPair).filter_by(symbol=symbol).first()
                
                if existing:
                    # 更新
                    existing.status = pair_info.get("status", status)
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    # 新增
                    crypto_pair = CryptoPair(
                        symbol=symbol,
                        base_asset=pair_info["base_asset"],
                        quote_asset=pair_info["quote_asset"],
                        exchange=self.exchange_name,
                        status=pair_info.get("status", status),
                    )
                    self.db.add(crypto_pair)
                
                updated_count += 1
            
            self.db.commit()
            logger.info(f"交易对同步完成: {updated_count}个")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"同步交易对失败: {e}")
            self.db.rollback()
            raise

    def sync_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> int:
        """
        同步K线数据

        Args:
            symbol: 交易对符号(如BTCUSDT)
            interval: K线周期(如1h, 4h, 1d)
            start_time: 开始时间
            end_time: 结束时间
            limit: 单次请求最大数量

        Returns:
            新增的K线数量
        """
        if interval not in self.SUPPORTED_INTERVALS:
            raise ValueError(f"不支持的K线周期: {interval}, 支持的周期: {self.SUPPORTED_INTERVALS}")
        
        logger.info(f"开始同步K线数据: {symbol}, interval={interval}")
        
        try:
            # 获取或创建K线表
            KlineTable = create_kline_table_class(interval)
            table_name = get_kline_table_name(interval)
            
            # 获取最新K线时间
            latest_kline = (
                self.db.query(KlineTable)
                .filter_by(symbol=symbol)
                .order_by(KlineTable.timestamp.desc())
                .first()
            )
            
            if latest_kline:
                # 增量同步:从最新K线的下一个周期开始
                sync_start = latest_kline.timestamp + self._get_interval_delta(interval)
                logger.info(f"增量同步: 从 {sync_start} 开始")
            else:
                # 全量同步:使用指定开始时间或默认7天前
                sync_start = start_time or datetime.now(timezone.utc) - timedelta(days=7)
                logger.info(f"全量同步: 从 {sync_start} 开始")
            
            sync_end = end_time or datetime.now(timezone.utc)
            
            # 分批获取K线数据
            total_inserted = 0
            current_start = sync_start
            
            while current_start < sync_end:
                # 获取K线数据
                klines_df = self.exchange.get_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=int(current_start.timestamp() * 1000),
                    end_time=int(sync_end.timestamp() * 1000),
                    limit=limit,
                )
                
                if klines_df.empty:
                    logger.info("没有更多K线数据")
                    break
                
                # 转换并插入数据库
                inserted = self._save_klines(klines_df, KlineTable, symbol)
                total_inserted += inserted
                
                logger.info(f"已同步 {inserted} 条K线, 总计 {total_inserted} 条")
                
                # 更新起始时间
                last_time = klines_df.iloc[-1]["timestamp"]
                current_start = last_time + self._get_interval_delta(interval)
                
                # 避免API限流
                time.sleep(0.1)
            
            logger.info(f"K线同步完成: {symbol}, {total_inserted}条")
            
            return total_inserted
            
        except Exception as e:
            logger.error(f"同步K线失败: {e}")
            self.db.rollback()
            raise

    def sync_all_klines(
        self,
        interval: str,
        symbols: list[str] | None = None,
        days_back: int = 7,
    ) -> dict[str, int]:
        """
        同步所有交易对的K线数据

        Args:
            interval: K线周期
            symbols: 交易对列表(None表示同步所有)
            days_back: 回溯天数

        Returns:
            每个交易对同步的K线数量
        """
        logger.info(f"开始批量同步K线数据: interval={interval}")
        
        # 获取交易对列表
        if symbols is None:
            pairs = (
                self.db.query(CryptoPair)
                .filter_by(status="trading")
                .filter_by(exchange=self.exchange_name)
                .all()
            )
            symbols = [pair.symbol for pair in pairs]
        
        results = {}
        start_time = datetime.now(timezone.utc) - timedelta(days=days_back)
        end_time = datetime.now(timezone.utc)
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"[{i+1}/{len(symbols)}] 同步 {symbol}")
                
                count = self.sync_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=start_time,
                    end_time=end_time,
                )
                
                results[symbol] = count
                
            except Exception as e:
                logger.error(f"同步 {symbol} 失败: {e}")
                results[symbol] = 0
        
        logger.info(f"批量同步完成: {len(results)}个交易对")
        
        return results

    def _save_klines(
        self,
        klines_df: pd.DataFrame,
        KlineTable: type,
        symbol: str,
    ) -> int:
        """
        保存K线数据到数据库

        Args:
            klines_df: K线数据DataFrame
            KlineTable: K线表类
            symbol: 交易对符号

        Returns:
            插入的数量
        """
        inserted_count = 0
        
        for _, row in klines_df.iterrows():
            # 检查是否已存在
            existing = (
                self.db.query(KlineTable)
                .filter_by(symbol=symbol, timestamp=row["timestamp"])
                .first()
            )
            
            if not existing:
                kline = KlineTable(
                    symbol=symbol,
                    timestamp=row["timestamp"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    quote_volume=row.get("quote_volume", 0),
                )
                self.db.add(kline)
                inserted_count += 1
        
        self.db.commit()
        
        return inserted_count

    @staticmethod
    def _get_interval_delta(interval: str) -> timedelta:
        """
        获取K线周期对应的时间增量

        Args:
            interval: K线周期

        Returns:
            时间增量
        """
        interval_map = {
            "1m": timedelta(minutes=1),
            "3m": timedelta(minutes=3),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "4h": timedelta(hours=4),
            "6h": timedelta(hours=6),
            "8h": timedelta(hours=8),
            "12h": timedelta(hours=12),
            "1d": timedelta(days=1),
            "3d": timedelta(days=3),
            "1w": timedelta(weeks=1),
            "1M": timedelta(days=30),
        }
        
        return interval_map.get(interval, timedelta(hours=1))
