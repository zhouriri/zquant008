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
加密货币同步任务执行器
"""

from typing import Dict, Any
from loguru import logger

from zquant.scheduler.base import TaskExecutor
from zquant.scheduler.utils import update_execution_progress
from zquant.data.crypto_sync import CryptoDataSync


class CryptoSyncExecutor(TaskExecutor):
    """加密货币同步任务执行器"""

    def __init__(self, task_type: str):
        """
        初始化执行器

        Args:
            task_type: 任务类型
        """
        self.task_type = task_type
        self.sync = CryptoDataSync()

    async def execute(
        self,
        db,
        config: Dict[str, Any],
        execution = None
    ) -> Dict[str, Any]:
        """
        执行同步任务

        Args:
            db: 数据库会话
            config: 任务配置字典
            execution: 执行记录对象

        Returns:
            执行结果字典
        """
        try:
            logger.info(f"开始执行加密货币同步任务: {self.task_type}")

            if self.task_type == "sync_pairs":
                return await self._sync_pairs(execution)
            elif self.task_type == "sync_klines":
                return await self._sync_klines(config, execution)
            elif self.task_type == "sync_all":
                return await self._sync_all(execution)
            else:
                raise ValueError(f"未知的任务类型: {self.task_type}")

        except Exception as e:
            logger.error(f"加密货币同步任务执行失败: {e}")
            if execution:
                update_execution_progress(
                    execution,
                    0,
                    f"执行失败: {str(e)}"
                )
            raise

    async def _sync_pairs(self, execution) -> Dict[str, Any]:
        """
        同步交易对列表

        Args:
            execution: 执行记录对象

        Returns:
            执行结果
        """
        update_execution_progress(execution, 10, "开始同步交易对")

        pairs = await self.sync.sync_pairs()

        update_execution_progress(
            execution,
            100,
            f"同步完成,共{len(pairs)}个交易对"
        )

        logger.info(f"交易对同步完成: {len(pairs)}个")

        return {
            "success": True,
            "count": len(pairs),
            "message": f"成功同步{len(pairs)}个交易对"
        }

    async def _sync_klines(
        self,
        config: Dict[str, Any],
        execution
    ) -> Dict[str, Any]:
        """
        同步K线数据

        Args:
            config: 任务配置
            execution: 执行记录对象

        Returns:
            执行结果
        """
        symbol = config.get("symbol")
        interval = config.get("interval", "1d")
        force = config.get("force", False)

        update_execution_progress(
            execution,
            10,
            f"开始同步 {symbol} {interval} K线"
        )

        count = await self.sync.sync_klines(
            symbol=symbol,
            interval=interval,
            force=force
        )

        update_execution_progress(
            execution,
            100,
            f"{symbol} {interval} K线同步完成"
        )

        logger.info(f"K线同步完成: {symbol} {interval}, {count}条")

        return {
            "success": True,
            "symbol": symbol,
            "interval": interval,
            "count": count,
            "message": f"成功同步{count}条K线数据"
        }

    async def _sync_all(self, execution) -> Dict[str, Any]:
        """
        批量同步所有数据

        Args:
            execution: 执行记录对象

        Returns:
            执行结果
        """
        update_execution_progress(execution, 10, "开始批量同步")

        # 获取热门交易对
        from zquant.repositories import CryptoPairRepository
        repo = CryptoPairRepository(execution)
        hot_pairs = repo.get_top_by_volume(20)

        total_count = 0
        total_symbols = len(hot_pairs)

        for i, pair in enumerate(hot_pairs):
            progress = 10 + (i / total_symbols) * 80
            update_execution_progress(
                execution,
                int(progress),
                f"同步 {pair.symbol} 1d K线 ({i+1}/{total_symbols})"
            )

            count = await self.sync.sync_klines(
                symbol=pair.symbol,
                interval="1d",
                force=False
            )
            total_count += count

        update_execution_progress(
            execution,
            100,
            f"批量同步完成,共{total_count}条K线"
        )

        logger.info(f"批量同步完成: {total_count}条K线")

        return {
            "success": True,
            "symbol_count": total_symbols,
            "kline_count": total_count,
            "message": f"成功批量同步{total_symbols}个交易对的K线数据"
        }
