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
加密货币实时行情同步任务
"""

from typing import Any

from loguru import logger
from sqlalchemy import select

from zquant.crypto import ExchangeFactory
from zquant.database import SessionLocal
from zquant.models.crypto import CryptoTicker
from zquant.repositories import CryptoPairRepository
from zquant.scheduler.job.base import BaseSyncJob


class SyncCryptoRealtimeJob(BaseSyncJob):
    """
    加密货币实时行情同步任务

    定期获取实时行情并存储到数据库
    """

    def __init__(self):
        super().__init__()
        self.exchange_client = None

    def execute(self, args: dict[str, Any]):
        """
        执行同步任务

        Args:
            args: 任务参数
                - exchange: 交易所名称
                - symbols: 交易对列表 (可选,默认获取热门交易对)
                - limit: 获取热门交易对数量 (默认10)
        """
        try:
            exchange = args.get("exchange", "binance")
            symbols = args.get("symbols")
            limit = args.get("limit", 10)

            logger.info(f"开始同步实时行情: exchange={exchange}")

            # 创建交易所客户端
            self.exchange_client = ExchangeFactory.create_exchange(
                exchange_name=exchange,
                api_key="",  # 获取行情不需要API密钥
                api_secret="",
            )

            # 创建数据库会话
            db = SessionLocal()

            try:
                # 获取要同步的交易对
                if symbols:
                    target_symbols = symbols
                else:
                    # 使用Repository获取热门交易对
                    pair_repo = CryptoPairRepository(db)
                    pairs = pair_repo.get_hot_pairs(limit=limit)
                    target_symbols = [pair.symbol for pair in pairs]

                logger.info(f"待同步交易对数量: {len(target_symbols)}")

                # 同步实时行情
                synced_count = 0
                for symbol in target_symbols:
                    try:
                        # 获取实时行情
                        ticker_data = self.exchange_client.get_ticker(symbol)

                        # 使用Repository风格的批量查询
                        stmt = (
                            select(CryptoTicker)
                            .where(
                                CryptoTicker.symbol == symbol,
                                CryptoTicker.exchange == exchange,
                            )
                        )
                        existing = db.execute(stmt).scalar_one_or_none()

                        if existing:
                            # 更新
                            existing.price = ticker_data["price"]
                            existing.price_change = ticker_data.get("price_change", 0)
                            existing.price_change_percent = ticker_data.get(
                                "price_change_percent", 0
                            )
                            existing.high_24h = ticker_data.get("high_24h", 0)
                            existing.low_24h = ticker_data.get("low_24h", 0)
                            existing.volume_24h = ticker_data.get("volume_24h", 0)
                            existing.updated_at = ticker_data.get("timestamp")
                        else:
                            # 新增
                            ticker = CryptoTicker(
                                symbol=symbol,
                                exchange=exchange,
                                price=ticker_data["price"],
                                price_change=ticker_data.get("price_change", 0),
                                price_change_percent=ticker_data.get(
                                    "price_change_percent", 0
                                ),
                                high_24h=ticker_data.get("high_24h", 0),
                                low_24h=ticker_data.get("low_24h", 0),
                                volume_24h=ticker_data.get("volume_24h", 0),
                                timestamp=ticker_data.get("timestamp"),
                            )
                            db.add(ticker)

                        synced_count += 1
                        logger.info(f"同步完成: {symbol}, 价格=${ticker_data['price']}")

                    except Exception as e:
                        logger.error(f"同步{symbol}失败: {e}")
                        continue

                db.commit()
                logger.info(f"实时行情同步完成: {synced_count}/{len(target_symbols)}个")

                return {"status": "success", "count": synced_count}

            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error(f"实时行情同步任务执行失败: {e}")
            raise
