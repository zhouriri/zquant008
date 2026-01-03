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
批量量化选股脚本

用于根据所有启用的选股策略执行批量选股，可以通过定时任务命令执行方式调用。

使用方法：
    python zquant/scheduler/job/batch_stock_filter.py [--start-date YYYYMMDD] [--end-date YYYYMMDD] [--strategy-id ID]

参数：
    --start-date YYYYMMDD: 开始日期（可选，默认最新交易日）
    --end-date YYYYMMDD: 结束日期（可选，默认最新交易日）
    --strategy-id ID: 指定执行的策略ID（可选，默认执行所有启用策略）
"""

import argparse
import os
from datetime import date, datetime
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 设置UTF-8编码
from zquant.utils.encoding import setup_utf8_encoding

setup_utf8_encoding()

from loguru import logger

from zquant.scheduler.job.base import BaseSyncJob
from zquant.services.stock_filter_task import StockFilterTaskService
from zquant.models.scheduler import TaskExecution

__job_name__ = "batch_stock_filter"


class BatchStockFilterJob(BaseSyncJob):
    """批量量化选股任务"""

    def __init__(self):
        super().__init__(__job_name__, "批量量化选股任务")

    def create_parser(self) -> argparse.ArgumentParser:
        parser = super().create_parser()
        # super().create_parser() 已经添加了 --start-date 和 --end-date
        parser.add_argument("--strategy-id", type=int, help="指定执行的策略ID（可选）")
        return parser

    def get_execution(self, db) -> TaskExecution | None:
        """
        从环境变量获取执行记录ID，并查询数据库获取执行记录对象
        """
        execution_id_str = os.environ.get("ZQUANT_EXECUTION_ID")
        if not execution_id_str:
            logger.debug("环境变量 ZQUANT_EXECUTION_ID 未设置，无法更新进度")
            return None

        try:
            execution_id = int(execution_id_str)
            execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
            if execution:
                logger.debug(f"获取到执行记录: {execution_id}")
                return execution
            else:
                logger.warning(f"执行记录 {execution_id} 不存在")
                return None
        except (ValueError, Exception) as e:
            logger.warning(f"获取执行记录失败: {e}")
            return None

    def execute(self, args: argparse.Namespace) -> int:
        strategy_id = args.strategy_id
        extra_info = self.build_extra_info()

        with self.db_session() as db:
            # 1. 验证和格式化日期
            try:
                # 判断是否所有日期参数都未传入
                all_params_empty = not args.start_date and not args.end_date
                
                start_date_str, end_date_str = self.validate_dates(
                    args.start_date, 
                    args.end_date, 
                    use_latest_trading_date_when_all_empty=all_params_empty
                )
            except ValueError as e:
                print(f"\n[错误] 日期参数验证失败: {e!s}")
                logger.error(f"日期参数验证失败: {e}")
                return 1

            # 转换日期对象
            start_date_obj = datetime.strptime(start_date_str, "%Y%m%d").date()
            end_date_obj = datetime.strptime(end_date_str, "%Y%m%d").date()

            # 获取执行记录（用于进度更新）
            execution = self.get_execution(db)

            # 打印开始信息
            self.print_start_info(
                开始日期=f"{start_date_str} ({start_date_obj.isoformat()})",
                结束日期=f"{end_date_str} ({end_date_obj.isoformat()})",
                策略ID=strategy_id if strategy_id else "全部",
            )

            # 2. 调用服务执行任务
            try:
                result = StockFilterTaskService.batch_execute_strategies(
                    db=db,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    strategy_id=strategy_id,
                    extra_info=extra_info,
                    execution=execution
                )

                # 3. 打印结束信息
                self.print_end_info(
                    success=result["success"],
                    总交易日=str(result.get("total_days", 0)),
                    成功次数=str(result.get("success_count", 0)),
                    失败次数=str(result.get("failed_count", 0)),
                    选中总数=str(result.get("total_results", 0)),
                    消息=result.get("message", "")
                )

                return 0 if result["success"] else 1

            except Exception as e:
                error_msg = f"批量选股任务执行异常: {e!s}"
                logger.error(error_msg)
                self.print_end_info(success=False, 错误=error_msg)
                return 1


def main():
    job = BatchStockFilterJob()
    sys.exit(job.run())


if __name__ == "__main__":
    main()
