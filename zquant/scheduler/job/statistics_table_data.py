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
数据表统计脚本

用于统计指定日期或日期范围的数据表入库情况，可以通过定时任务命令执行方式调用。

使用方法：
    python zquant/scheduler/job/statistics_table_data.py [--start-date YYYYMMDD] [--end-date YYYYMMDD]

参数：
    --start-date YYYYMMDD: 开始日期（可选，默认今天）
    --end-date YYYYMMDD: 结束日期（可选，默认今天）
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
from zquant.services.data import DataService
from zquant.models.scheduler import TaskExecution
from zquant.scheduler.utils import update_execution_progress

__job_name__ = "statistics_table_data"


class StatisticsTableDataJob(BaseSyncJob):
    """数据表统计任务"""

    def __init__(self):
        super().__init__(__job_name__, "数据表统计任务")

    def create_parser(self) -> argparse.ArgumentParser:
        # 使用基类的 create_parser，已经包含 --start-date 和 --end-date
        return super().create_parser()

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
            )

            # 2. 获取日期范围内的所有日期（包括非交易日）
            from datetime import timedelta
            all_dates = []
            current_date = start_date_obj
            while current_date <= end_date_obj:
                all_dates.append(current_date)
                current_date += timedelta(days=1)

            total_dates = len(all_dates)
            processed_dates = 0
            success_count = 0
            failed_count = 0
            total_tables = 0
            failed_details = []

            # 初始化进度
            update_execution_progress(
                db,
                execution,
                total_items=total_dates,
                processed_items=0,
                message=f"开始数据表统计: {len(all_dates)} 天"
            )

            # 3. 循环处理每个日期
            for current_date in all_dates:
                processed_dates += 1
                try:
                    # 更新进度
                    update_execution_progress(
                        db,
                        execution,
                        processed_items=processed_dates - 1,
                        current_item=current_date.isoformat(),
                        message=f"正在统计: {current_date.isoformat()} ({processed_dates}/{total_dates})"
                    )

                    # 调用服务执行统计
                    results = DataService.statistics_table_data(
                        db=db,
                        stat_date=current_date,
                        created_by="scheduler",
                        execution=execution
                    )

                    success_count += 1
                    total_tables += len(results)
                    logger.info(f"日期 {current_date} 统计完成，共统计 {len(results)} 个表")

                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    failed_details.append({
                        "date": current_date.isoformat(),
                        "error": error_msg
                    })
                    logger.error(f"日期 {current_date} 统计失败: {error_msg}")

            # 4. 完成更新
            update_execution_progress(
                db,
                execution,
                processed_items=total_dates,
                message=f"数据表统计完成: 成功={success_count}, 失败={failed_count}, 总表数={total_tables}"
            )

            # 5. 打印结束信息
            success = failed_count == 0
            self.print_end_info(
                success=success,
                总天数=str(total_dates),
                成功天数=str(success_count),
                失败天数=str(failed_count),
                总表数=str(total_tables),
                消息=f"数据表统计完成: 成功={success_count}天, 失败={failed_count}天, 总表数={total_tables}"
            )

            return 0 if failed_count == 0 else 1


def main():
    job = StatisticsTableDataJob()
    sys.exit(job.run())


if __name__ == "__main__":
    main()

