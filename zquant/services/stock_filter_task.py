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
量化选股任务服务层
"""

import json
from datetime import date
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy.orm import Session

from zquant.models.data import StockFilterResult, StockFilterStrategy
from zquant.services.stock_filter import StockFilterService
from zquant.models.scheduler import TaskExecution
from zquant.scheduler.utils import update_execution_progress
from sqlalchemy import text


class StockFilterTaskService:
    """量化选股任务服务"""

    @classmethod
    def execute_strategy(
        cls, db: Session, strategy: StockFilterStrategy | int, trade_date: Optional[date] = None
    ) -> dict[str, Any]:
        """
        执行单个策略并保存结果

        Args:
            db: 数据库会话
            strategy: 策略对象或策略ID
            trade_date: 交易日期，如果不提供则自动获取最新交易日期

        Returns:
            执行结果
        """
        if isinstance(strategy, int):
            strategy = db.query(StockFilterStrategy).filter(StockFilterStrategy.id == strategy).first()
            if not strategy:
                return {"success": False, "message": f"未找到策略 ID: {strategy}"}

        if not trade_date:
            trade_date = cls.get_latest_trade_date(db)

        try:
            # 1. 解析策略配置
            filter_conditions = json.loads(strategy.filter_conditions) if strategy.filter_conditions else None
            sort_config = json.loads(strategy.sort_config) if strategy.sort_config else None
            
            # 2. 执行选股 - 查询完整数据（包含反范式化字段）
            # 设置 selected_columns 为 None，触发 StockFilterService 使用模型定义的全部列
            selected_columns = None
            
            items, total = StockFilterService.get_filter_results(
                db=db,
                trade_date=trade_date,
                filter_conditions=filter_conditions,
                selected_columns=selected_columns,
                sort_config=sort_config,
                skip=0,
                limit=5000, # 选股结果通常不会超过5000条
            )
            
            # 3. 清除旧结果
            db.query(StockFilterResult).filter(
                StockFilterResult.trade_date == trade_date,
                StockFilterResult.strategy_id == strategy.id
            ).delete()
            
            # 4. 保存新结果（使用反范式化的保存方法）
            if items:
                saved_count = StockFilterService.save_filter_results(
                    db=db,
                    trade_date=trade_date,
                    strategy_id=strategy.id,
                    strategy_name=strategy.name,
                    stock_data=items,  # 传递完整的股票数据
                    username=None,
                )
            else:
                saved_count = 0
                db.commit()
            
            logger.info(f"策略 '{strategy.name}' 在 {trade_date} 执行完成，选中 {saved_count} 只股票")
            
            return {
                "success": True, 
                "message": f"策略 '{strategy.name}' 执行完成", 
                "count": saved_count,
                "trade_date": trade_date
            }

        except Exception as e:
            db.rollback()
            logger.error(f"执行策略 '{strategy.name}' 失败: {e}")
            return {"success": False, "message": str(e)}

    @classmethod
    def batch_execute_strategies(
        cls,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        strategy_id: Optional[int] = None,
        extra_info: Optional[Dict[str, Any]] = None,
        execution: Optional[TaskExecution] = None,
    ) -> dict[str, Any]:
        """
        批量执行量化选股策略（支持多日期和指定策略）

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            strategy_id: 指定策略ID（可选）
            extra_info: 额外信息
            execution: 执行记录对象（可选）

        Returns:
            执行结果汇总
        """
        # 1. 处理日期范围
        if not start_date or not end_date:
            latest_date = cls.get_latest_trade_date(db)
            start_date = start_date or latest_date
            end_date = end_date or latest_date

        from zquant.utils.date_helper import DateHelper
        trading_dates = DateHelper.get_trading_dates(db, start_date, end_date)
        if not trading_dates:
            return {"success": True, "message": "日期范围内无交易日", "total_days": 0, "total_results": 0}

        # 2. 获取策略列表
        if strategy_id:
            strategy = db.query(StockFilterStrategy).filter(StockFilterStrategy.id == strategy_id).first()
            strategies = [strategy] if strategy else []
        else:
            strategies = db.query(StockFilterStrategy).all()

        if not strategies:
            return {"success": True, "message": "未找到有效策略", "total_strategies": 0, "total_results": 0}

        # 3. 初始化进度
        total_days = len(trading_dates)
        total_strategies = len(strategies)
        total_items = total_days * total_strategies
        processed_items = 0
        total_results = 0
        success_count = 0
        failed_count = 0
        failed_details = []

        update_execution_progress(
            db, 
            execution, 
            total_items=total_items, 
            processed_items=0, 
            message=f"开始批量选股任务: {len(trading_dates)}天 x {len(strategies)}个策略"
        )

        # 4. 循环执行
        for current_date in trading_dates:
            for strategy in strategies:
                processed_items += 1
                try:
                    # 更新进度
                    update_execution_progress(
                        db,
                        execution,
                        processed_items=processed_items - 1,
                        current_item=f"{current_date} | {strategy.name}",
                        message=f"正在执行: {strategy.name} ({current_date})",
                    )

                    # 记录日志
                    logger.info(
                        f"量化选股进度: {current_date} | {strategy.name} - "
                        f"已处理 {processed_items}/{total_items} "
                        f"(成功={success_count}, 失败={failed_count}, 总结果={total_results})"
                    )

                    res = cls.execute_strategy(db, strategy, current_date)
                    if res["success"]:
                        success_count += 1
                        total_results += res["count"]
                    else:
                        failed_count += 1
                        failed_details.append({
                            "date": str(current_date),
                            "strategy": strategy.name,
                            "error": res["message"]
                        })

                except Exception as e:
                    if "Task terminated" in str(e):
                        raise
                    logger.error(f"执行选股异常 ({current_date} | {strategy.name}): {e}")
                    failed_count += 1
                    failed_details.append({
                        "date": str(current_date),
                        "strategy": strategy.name,
                        "error": str(e)
                    })

        # 5. 完成更新
        update_execution_progress(
            db, 
            execution, 
            processed_items=total_items, 
            message=f"批量选股任务完成: 成功={success_count}, 失败={failed_count}, 总数={total_results}"
        )

        return {
            "success": failed_count == 0,
            "message": f"任务完成: 成功={success_count}, 失败={failed_count}, 结果={total_results}",
            "total_days": total_days,
            "total_strategies": total_strategies,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_results": total_results,
            "failed_details": failed_details,
        }

    @classmethod
    def batch_execute_all_strategies(
        cls,
        db: Session,
        trade_date: Optional[date] = None,
        extra_info: Optional[Dict[str, Any]] = None,
        execution: Optional[TaskExecution] = None,
    ) -> dict[str, Any]:
        """
        批量执行所有量化选股策略并保存结果（为了兼容旧调用，转发给新方法）
        """
        return cls.batch_execute_strategies(
            db=db,
            start_date=trade_date,
            end_date=trade_date,
            extra_info=extra_info,
            execution=execution
        )

    @classmethod
    def get_latest_trade_date(cls, db: Session) -> date:
        """获取数据库中最小的有数据的交易日期（通常建议是最近的一个交易日）"""
        try:
            # 从 zq_data_tustock_daily 视图中获取最后一条交易记录的日期
            from zquant.models.data import TUSTOCK_DAILY_VIEW_NAME
            sql = f"SELECT MAX(trade_date) FROM `{TUSTOCK_DAILY_VIEW_NAME}`"
            result = db.execute(text(sql)).scalar()
            if result:
                if isinstance(result, str):
                    return date.fromisoformat(result)
                return result
        except Exception as e:
            logger.warning(f"获取最新交易日期失败: {e}")
        
        return date.today()
