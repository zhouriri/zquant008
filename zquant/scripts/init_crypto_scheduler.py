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
初始化加密货币调度任务
"""

import os
from datetime import datetime

from zquant.database import SessionLocal
from zquant.models.scheduler import ScheduledTask, TaskType
from zquant.scheduler.job.sync_crypto_klines import (
    SyncCryptoKlinesJob,
    SyncCryptoPairsJob,
    SyncCryptoRealtimeJob,
)


def init_crypto_scheduler_jobs():
    """
    初始化加密货币相关调度任务

    需要在环境变量中配置API密钥:
    - BINANCE_API_KEY
    - BINANCE_API_SECRET
    - OKX_API_KEY
    - OKX_API_SECRET
    - OKX_PASSPHRASE
    """

    print("=" * 60)
    print("初始化加密货币调度任务")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 检查API密钥
        binance_api_key = os.getenv("BINANCE_API_KEY")
        binance_api_secret = os.getenv("BINANCE_API_SECRET")

        if not binance_api_key or not binance_api_secret:
            print("⚠️  警告: 未配置BINANCE_API_KEY和BINANCE_API_SECRET环境变量")
            print("将跳过币安相关任务初始化")
            return

        # 创建任务
        tasks = [
            # 每小时同步1小时K线
            ScheduledTask(
                name="同步币安1小时K线",
                task_type=TaskType.SYNC,
                job_class="zquant.scheduler.job.sync_crypto_klines.SyncCryptoKlinesJob",
                args={
                    "exchange": "binance",
                    "interval": "1h",
                    "api_key": binance_api_key,
                    "api_secret": binance_api_secret,
                },
                cron_expression="0 * * * *",  # 每小时
                enabled=True,
                description="每5分钟同步主要交易对的1小时K线数据",
            ),
            # 每5分钟同步实时行情
            ScheduledTask(
                name="同步币安实时行情",
                task_type=TaskType.SYNC,
                job_class="zquant.scheduler.job.sync_crypto_klines.SyncCryptoRealtimeJob",
                args={
                    "exchange": "binance",
                    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
                },
                cron_expression="*/5 * * * *",  # 每5分钟
                enabled=True,
                description="每5分钟同步主要交易对的实时行情",
            ),
            # 每天同步交易对列表
            ScheduledTask(
                name="同步币安交易对列表",
                task_type=TaskType.SYNC,
                job_class="zquant.scheduler.job.sync_crypto_klines.SyncCryptoPairsJob",
                args={
                    "exchange": "binance",
                    "quote_asset": "USDT",
                    "api_key": binance_api_key,
                    "api_secret": binance_api_secret,
                },
                cron_expression="0 0 * * *",  # 每天0点
                enabled=True,
                description="每天同步USDT交易对列表",
            ),
        ]

        # 创建或更新任务
        for task_data in tasks:
            # 检查是否已存在
            existing = (
                db.query(ScheduledTask).filter_by(name=task_data.name).first()
            )

            if existing:
                print(f"✓ 任务已存在: {task_data.name}")
                # 更新任务参数
                existing.job_class = task_data.job_class
                existing.args = task_data.args
                existing.cron_expression = task_data.cron_expression
                existing.description = task_data.description
                existing.updated_at = datetime.now()
            else:
                db.add(task_data)
                print(f"✓ 创建任务: {task_data.name}")

        db.commit()

        print("\n" + "=" * 60)
        print("加密货币调度任务初始化完成!")
        print("=" * 60)
        print("\n任务列表:")
        for task in tasks:
            print(f"  - {task.name}: {task.cron_expression}")

    except Exception as e:
        db.rollback()
        print(f"\n初始化失败: {e}")
        raise
    finally:
        db.close()


def list_crypto_jobs():
    """列出所有加密货币相关任务"""
    db = SessionLocal()

    try:
        tasks = (
            db.query(ScheduledTask)
            .filter(ScheduledTask.job_class.like("%crypto%"))
            .all()
        )

        print("\n加密货币相关任务:")
        print("-" * 60)

        for task in tasks:
            status = "启用" if task.enabled else "禁用"
            print(f"  [{status}] {task.name}")
            print(f"    Cron: {task.cron_expression}")
            print(f"    描述: {task.description}")
            print("-" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_crypto_jobs()
    else:
        init_crypto_scheduler_jobs()
        print("\n使用 'python init_crypto_scheduler.py --list' 查看任务列表")
