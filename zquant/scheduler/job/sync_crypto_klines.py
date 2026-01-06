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
加密货币K线数据同步任务
"""

from typing import Any

from loguru import logger

from zquant.scheduler.job.base import BaseSyncJob
from zquant.scheduler.executors.crypto_sync_executor import CryptoSyncExecutor
from zquant.scheduler.job.sync_crypto_realtime import SyncCryptoRealtimeJob


class SyncCryptoKlinesJob(BaseSyncJob):
    """
    加密货币K线数据同步任务

    定期同步指定交易对的K线数据到数据库
    """

    def __init__(self):
        super().__init__()
        self.executor = None

    def execute(self, args: dict[str, Any]):
        """
        执行同步任务

        Args:
            args: 任务参数
                - exchange: 交易所名称 (binance/okx/bybit)
                - interval: K线周期 (1h/4h/1d)
                - symbols: 交易对列表 (可选,默认同步所有USDT交易对)
                - quote_asset: 计价资产 (默认USDT)
                - api_key: API密钥
                - api_secret: API密钥
                - passphrase: API密钥 (OKX需要)
        """
        try:
            # 创建执行器
            self.executor = CryptoSyncExecutor(
                exchange=args.get("exchange", "binance"),
                interval=args.get("interval", "1h"),
                api_key=args.get("api_key"),
                api_secret=args.get("api_secret"),
                passphrase=args.get("passphrase"),
            )

            # 准备参数
            symbols = args.get("symbols")
            quote_asset = args.get("quote_asset", "USDT")
            days_back = args.get("days_back", 1)

            # 执行同步K线任务
            logger.info(f"开始K线同步任务: {self.executor.exchange}, {self.executor.interval}")
            result = self.executor.execute(
                task_type="sync_klines",
                symbols=symbols,
                quote_asset=quote_asset,
                days_back=days_back,
            )

            logger.info(f"K线同步任务完成: {result}")
            return result

        except Exception as e:
            logger.error(f"K线同步任务执行失败: {e}")
            raise


class SyncCryptoPairsJob(BaseSyncJob):
    """
    加密货币交易对列表同步任务

    定期同步交易对列表到数据库
    """

    def __init__(self):
        super().__init__()
        self.executor = None

    def execute(self, args: dict[str, Any]):
        """
        执行同步任务

        Args:
            args: 任务参数
                - exchange: 交易所名称
                - quote_asset: 计价资产 (默认USDT)
                - status: 交易状态 (默认trading)
                - api_key: API密钥
                - api_secret: API密钥
                - passphrase: API密钥 (OKX需要)
        """
        try:
            # 创建执行器
            self.executor = CryptoSyncExecutor(
                exchange=args.get("exchange", "binance"),
                api_key=args.get("api_key"),
                api_secret=args.get("api_secret"),
                passphrase=args.get("passphrase"),
            )

            # 准备参数
            quote_asset = args.get("quote_asset", "USDT")
            status = args.get("status", "trading")

            # 执行同步交易对任务
            logger.info(f"开始交易对同步任务: {self.executor.exchange}")
            result = self.executor.execute(
                task_type="sync_pairs",
                quote_asset=quote_asset,
                status=status,
            )

            logger.info(f"交易对同步任务完成: {result}")
            return result

        except Exception as e:
            logger.error(f"交易对同步任务执行失败: {e}")
            raise


class SyncCryptoRealtimeJob(BaseSyncJob):
    """
    加密货币实时行情同步任务
    
    定期获取实时行情并存储到数据库
    """

    def __init__(self):
        super().__init__()

    def execute(self, args: dict[str, Any]):
        """
        执行同步任务

        Args:
            args: 任务参数
                - exchange: 交易所名称
                - symbols: 交易对列表
        """
        try:
            from zquant.crypto import ExchangeFactory
            from zquant.models.crypto import CryptoTicker

            exchange = args.get("exchange", "binance")
            symbols = args.get("symbols", ["BTCUSDT", "ETHUSDT"])

            logger.info(f"开始同步实时行情: exchange={exchange}")

            # 创建交易所客户端
            exchange_client = ExchangeFactory.create_exchange(
                exchange_name=exchange,
                api_key="",  # 获取行情不需要API密钥
                api_secret="",
            )

            # 创建数据库会话
            db = SessionLocal()

            try:
                synced_count = 0
                for symbol in symbols:
                    # 获取实时行情
                    ticker_data = exchange_client.get_ticker(symbol)

                    # 查询是否已存在
                    existing = (
                        db.query(CryptoTicker)
                        .filter_by(symbol=symbol, exchange=exchange)
                        .first()
                    )

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

                db.commit()
                logger.info(f"实时行情同步完成: {synced_count}个交易对")

                return {"status": "success", "count": synced_count}

            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error(f"实时行情同步任务执行失败: {e}")
            raise
