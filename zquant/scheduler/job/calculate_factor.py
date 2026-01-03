# Copyright 2025 ZQuant Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Apache License is distributed on an "AS IS" BASIS,
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
量化因子计算脚本
支持计算单个因子或所有启用的因子

使用方法：
    python zquant/scheduler/job/calculate_factor.py [--factor-id FACTOR_ID] [--codes CODE1,CODE2] [--start-date YYYYMMDD] [--end-date YYYYMMDD]

参数：
    --factor-id FACTOR_ID: 因子ID（可选，不指定则计算所有启用的因子）
    --codes CODE1,CODE2: 股票代码列表，逗号分隔（可选，如：000001.SZ,600000.SH，不指定则计算所有股票）
    --start-date YYYYMMDD: 开始日期（可选，默认：最后一个交易日）
    --end-date YYYYMMDD: 结束日期（可选，默认：最后一个交易日）

注意：
    - 开始日期不能大于结束日期
    - 结束日期不能超过当天日期
    - 如果未指定任何日期参数，则开始日期和结束日期都默认为最后一个交易日
    - 如果不指定factor-id，将计算所有启用的因子（可能耗时较长）
    - 如果不指定codes，将计算所有股票（可能耗时较长）
"""

import argparse
import os
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 设置UTF-8编码
from zquant.utils.encoding import setup_utf8_encoding

setup_utf8_encoding()

from loguru import logger

from zquant.scheduler.job.base import BaseSyncJob
from zquant.services.factor_calculation import FactorCalculationService
from zquant.models.scheduler import TaskExecution

__job_name__ = "calculate_factor"


class CalculateFactorJob(BaseSyncJob):
    """量化因子计算任务"""

    def __init__(self):
        super().__init__(__job_name__, "量化因子计算任务")

    def create_parser(self) -> argparse.ArgumentParser:
        parser = super().create_parser()
        parser.add_argument("--factor-id", type=int, help="因子ID（可选，不指定则计算所有启用的因子）")
        parser.add_argument(
            "--codes", type=str, help="股票代码列表，逗号分隔（可选，如：000001.SZ,600000.SH，不指定则计算所有股票）"
        )
        return parser

    def get_execution(self, db) -> TaskExecution | None:
        """
        从环境变量获取执行记录ID，并查询数据库获取执行记录对象

        Args:
            db: 数据库会话

        Returns:
            执行记录对象，如果环境变量未设置或查询失败则返回None
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
        # 解析 factor_id
        factor_id = args.factor_id if args.factor_id else None

        # 解析 codes
        codes = None
        if args.codes:
            codes = [code.strip() for code in args.codes.split(",") if code.strip()]
            if not codes:
                codes = None

        # 构建 extra_info
        extra_info = self.build_extra_info()

        with self.db_session() as db:
            # 验证和格式化日期（如果未传任何参数，默认使用最后一个交易日）
            try:
                start_date, end_date = self.validate_dates(
                    args.start_date, args.end_date, default_start_days=0, use_latest_trading_date_when_all_empty=True
                )
            except ValueError as e:
                print(f"\n[错误] 日期参数验证失败: {e!s}")
                logger.error(f"日期参数验证失败: {e}")
                return 1

            # 转换日期格式（FactorCalculationService需要date对象）
            start_date_obj = datetime.strptime(start_date, "%Y%m%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y%m%d").date()

            # 获取执行记录（用于进度更新）
            execution = self.get_execution(db)

            # 打印开始信息
            factor_info = f"因子ID: {factor_id}" if factor_id else "全部启用的因子"
            codes_info = f"股票代码: {', '.join(codes[:5])}{'...' if codes and len(codes) > 5 else ''}" if codes else "全部股票"
            self.print_start_info(
                因子=factor_info,
                股票=codes_info,
                开始日期=f"{start_date} ({start_date_obj.strftime('%Y-%m-%d')})",
                结束日期=f"{end_date} ({end_date_obj.strftime('%Y-%m-%d')})",
            )

            # 执行因子计算
            logger.info(f"开始计算因子: factor_id={factor_id}, codes={codes}, start_date={start_date_obj}, end_date={end_date_obj}")
            try:
                result = FactorCalculationService.calculate_factor(
                    db=db,
                    factor_id=factor_id,
                    codes=codes,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    extra_info=extra_info,
                    execution=execution,
                )

                if result["success"]:
                    logger.info(
                        f"因子计算完成: 成功={result['calculated_count']}, "
                        f"数据不完整={result.get('invalid_count', 0)}, 失败={result['failed_count']}"
                    )
                    self.print_end_info(
                        success=True,
                        成功计算数=str(result["calculated_count"]),
                        数据不完整数=str(result.get("invalid_count", 0)),
                        失败数=str(result["failed_count"]),
                        消息=result.get("message", ""),
                    )
                    return 0
                else:
                    logger.error(f"因子计算失败: {result.get('message', '未知错误')}")
                    self.print_end_info(
                        success=False,
                        消息=result.get("message", "未知错误"),
                    )
                    return 1

            except Exception as e:
                error_msg = f"因子计算异常: {e!s}"
                logger.error(error_msg)
                self.print_end_info(success=False, 错误=error_msg)
                return 1


def main():
    job = CalculateFactorJob()
    sys.exit(job.run())


if __name__ == "__main__":
    main()

