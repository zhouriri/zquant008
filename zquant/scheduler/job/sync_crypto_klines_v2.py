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
加密货币回测任务调度
"""

from typing import Any

from loguru import logger

from zquant.backtest.crypto_engine import CryptoBacktestEngine
from zquant.strategies.crypto_strategies import (
    SimpleMACryptoStrategy,
    BreakoutCryptoStrategy,
    GridTradingCryptoStrategy,
    RSICryptoStrategy,
    TrendFollowCryptoStrategy,
)
from zquant.models.backtest import BacktestResult, BacktestTask, BacktestStatus, Strategy
from zquant.repositories import CryptoKlineRepository
from zquant.database import SessionLocal
from datetime import datetime, timedelta, timezone


STRATEGY_MAP = {
    "SimpleMACryptoStrategy": SimpleMACryptoStrategy,
    "BreakoutCryptoStrategy": BreakoutCryptoStrategy,
    "GridTradingCryptoStrategy": GridTradingCryptoStrategy,
    "RSICryptoStrategy": RSICryptoStrategy,
    "TrendFollowCryptoStrategy": TrendFollowCryptoStrategy,
}


class CryptoBacktestJob:
    """加密货币回测任务"""

    def __init__(self):
        self.db = None
        self.kline_repo = None

    def execute(self, args: dict[str, Any]):
        """
        执行回测任务

        Args:
            args: 任务参数
                - strategy_name: 策略名称
                - symbol: 交易对
                - interval: K线周期
                - start_time: 开始时间
                - end_time: 结束时间
                - initial_capital: 初始资金
                - exchange: 交易所
                - maker_fee: Maker费率
                - taker_fee: Taker费率
                - slippage_rate: 滑点率
        """
        try:
            strategy_name = args.get("strategy_name", "SimpleMACryptoStrategy")
            symbol = args.get("symbol", "BTCUSDT")
            interval = args.get("interval", "1h")
            start_time_str = args.get("start_time")
            end_time_str = args.get("end_time")
            initial_capital = args.get("initial_capital", 10000.0)
            exchange = args.get("exchange", "binance")
            maker_fee = args.get("maker_fee", 0.001)
            taker_fee = args.get("taker_fee", 0.001)
            slippage_rate = args.get("slippage_rate", 0.0005)
            task_id = args.get("task_id")

            # 获取策略类
            strategy_class = STRATEGY_MAP.get(strategy_name)
            if not strategy_class:
                raise ValueError(f"未找到策略: {strategy_name}")

            # 解析时间
            start_time = (
                datetime.fromisoformat(start_time_str)
                if start_time_str
                else datetime.now(timezone.utc) - timedelta(days=30)
            )
            end_time = (
                datetime.fromisoformat(end_time_str)
                if end_time_str
                else datetime.now(timezone.utc)
            )

            logger.info(f"开始执行加密货币回测: {strategy_name}")

            # 使用Repository验证K线数据
            self.db = SessionLocal()
            self.kline_repo = CryptoKlineRepository(self.db)

            # 检查K线数据是否充足
            klines = self.kline_repo.get_by_time_range(symbol, interval, start_time, end_time)
            if len(klines) == 0:
                logger.warning(f"没有找到K线数据: {symbol} {interval}")
                return {"status": "skipped", "reason": "no_kline_data"}

            logger.info(f"找到{len(klines)}条K线数据")

            # 创建回测配置
            config = {
                "initial_capital": initial_capital,
                "exchange": exchange,
                "symbols": [symbol],
                "interval": interval,
                "start_time": start_time,
                "end_time": end_time,
                "maker_fee": maker_fee,
                "taker_fee": taker_fee,
                "slippage_rate": slippage_rate,
            }

            # 执行回测
            engine = CryptoBacktestEngine(strategy_class, config)
            results = engine.run()

            # 保存回测结果
            self._save_backtest_result(
                task_id=task_id,
                strategy_name=strategy_name,
                symbol=symbol,
                interval=interval,
                config=config,
                results=results,
            )

            logger.info(f"回测完成: 收益率 {results['total_return_pct']:.2f}%")

            return results

        except Exception as e:
            logger.error(f"回测任务执行失败: {e}")
            raise
        finally:
            if self.db:
                self.db.close()

    def _save_backtest_result(
        self,
        task_id: int | None,
        strategy_name: str,
        symbol: str,
        interval: str,
        config: dict,
        results: dict,
    ):
        """
        保存回测结果

        Args:
            task_id: 任务ID
            strategy_name: 策略名称
            symbol: 交易对
            interval: K线周期
            config: 回测配置
            results: 回测结果
        """
        try:
            # 创建或获取策略记录
            strategy = self.db.query(Strategy).filter_by(name=strategy_name).first()
            if not strategy:
                strategy = Strategy(name=strategy_name, description=strategy_name)
                self.db.add(strategy)
                self.db.flush()

            # 更新任务状态
            if task_id:
                task = self.db.query(BacktestTask).filter_by(id=task_id).first()
                if task:
                    task.status = BacktestStatus.COMPLETED
                    task.end_time = datetime.now(timezone.utc)
            else:
                # 创建新任务
                task = BacktestTask(
                    status=BacktestStatus.COMPLETED,
                    start_time=config["start_time"],
                    end_time=config["end_time"],
                )
                self.db.add(task)
                self.db.flush()

            # 创建回测结果
            result = BacktestResult(
                task_id=task.id,
                strategy_id=strategy.id,
                symbol=symbol,
                initial_capital=results["initial_capital"],
                final_capital=results["final_value"],
                total_return=results["total_return"],
                total_trades=results["total_trades"],
                # TODO: 添加更多指标
                win_rate=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
            )
            self.db.add(result)

            self.db.commit()
            logger.info("回测结果已保存")

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存回测结果失败: {e}")
            raise
