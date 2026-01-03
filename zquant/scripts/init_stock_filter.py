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
量化选股策略初始化脚本
初始化默认的选股策略配置
"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).resolve().parent  # zquant/scripts
zquant_dir = script_dir.parent  # zquant 目录
project_root = zquant_dir.parent  # 项目根目录
sys.path.insert(0, str(project_root))

from loguru import logger

from zquant.database import SessionLocal, engine, Base
from zquant.data.storage_base import ensure_table_exists
from zquant.models.data import StockFilterStrategy
from zquant.models.user import User
from zquant.services.stock_filter import StockFilterService


def create_stock_filter_table():
    """
    创建量化选股过滤及结果表

    Returns:
        是否成功
    """
    logger.info("检查并创建量化选股过滤及结果表...")
    try:
        db = SessionLocal()
        try:
            # 创建策略表
            from zquant.models.data import StockFilterResult
            success_strategy = ensure_table_exists(db, StockFilterStrategy)
            # 创建结果表
            success_result = ensure_table_exists(db, StockFilterResult)
            
            if success_strategy and success_result:
                logger.info("✓ 量化选股过滤及结果表检查/创建完成")
                return True
            return False
        finally:
            db.close()
    except Exception as e:
        logger.error(f"创建量化选股表失败: {e}")
        return False


def init_stock_filter_strategies(force: bool = False):
    """
    初始化量化选股过滤策略

    Args:
        force: 是否强制重新创建（删除已存在的策略）
    """
    logger.info("=" * 60)
    logger.info("初始化量化选股过滤策略")
    logger.info("=" * 60)

    # 首先创建表（如果不存在）
    if not create_stock_filter_table():
        logger.error("创建量化选股过滤表失败，终止初始化")
        return False

    db = SessionLocal()
    try:
        # 获取管理员用户（如果没有则使用第一个用户）
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = db.query(User).first()
            if not admin_user:
                logger.error("未找到用户，请先初始化数据库")
                return False

        logger.info(f"使用用户: {admin_user.username} (ID: {admin_user.id})")

        # 定义默认策略配置
        # 策略：成交额>10亿 AND 换手率>=10% AND (总市值在50~200亿 OR 流通市值在50~200亿)
        default_strategy = {
            "name": "活跃股票筛选",
            "description": "筛选成交额>10亿、换手率>=10%、市值在50~200亿之间的活跃股票",
            "filter_conditions": {
                "logic": "AND",
                "conditions": [
                    {"field": "amount", "operator": ">", "value": 10, "not": False},
                    {"field": "turnover_rate", "operator": ">=", "value": 10, "not": False},
                    {
                        "logic": "OR",
                        "conditions": [
                            {
                                "field": "total_mv",
                                "operator": "BETWEEN",
                                "value": [50, 200],
                                "not": False,
                            },
                            {
                                "field": "circ_mv",
                                "operator": "BETWEEN",
                                "value": [50, 200],
                                "not": False,
                            },
                        ],
                        "not": False,
                    },
                ],
                "not": False,
            },
            "selected_columns": [
                "ts_code",
                "symbol",
                "name",
                "industry",
                "amount",
                "turnover_rate",
                "total_mv",
                "circ_mv",
                "pe",
                "pb",
                "pct_chg",
            ],
            "sort_config": [
                {"field": "amount", "order": "desc"},
                {"field": "turnover_rate", "order": "desc"},
            ],
        }

        # 检查策略是否已存在
        existing_strategy = (
            db.query(StockFilterStrategy)
            .filter(
                StockFilterStrategy.user_id == admin_user.id,
                StockFilterStrategy.name == default_strategy["name"],
            )
            .first()
        )

        if existing_strategy:
            if force:
                logger.info(f"删除已存在的策略: {default_strategy['name']}")
                db.delete(existing_strategy)
                db.commit()
            else:
                logger.info(f"策略已存在，跳过: {default_strategy['name']}")
                return True

        # 创建策略
        logger.info(f"创建策略: {default_strategy['name']}")
        strategy = StockFilterService.save_strategy(
            db=db,
            user_id=admin_user.id,
            name=default_strategy["name"],
            description=default_strategy["description"],
            filter_conditions=default_strategy["filter_conditions"],
            selected_columns=default_strategy["selected_columns"],
            sort_config=default_strategy["sort_config"],
            created_by=admin_user.username,
        )

        logger.info(f"✓ 成功创建策略: {strategy.name} (ID: {strategy.id})")
        logger.info("=" * 60)
        logger.info("量化选股过滤策略初始化完成")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"初始化量化选股过滤策略失败: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="初始化量化选股过滤策略")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新创建（删除已存在的策略）",
    )
    parser.add_argument(
        "--tables-only",
        action="store_true",
        help="只创建表，不创建策略数据",
    )
    args = parser.parse_args()

    if args.tables_only:
        # 只创建表
        success = create_stock_filter_table()
    else:
        # 创建表并初始化策略
        success = init_stock_filter_strategies(force=args.force)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
