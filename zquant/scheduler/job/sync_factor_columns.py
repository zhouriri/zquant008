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
因子分表列同步脚本

用于同步所有因子分表(zq_quant_factor_spacex_*)的列结构，确保所有分表的列一致。

使用方法：
    python zquant/scheduler/job/sync_factor_columns.py
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 设置UTF-8编码
from zquant.utils.encoding import setup_utf8_encoding

setup_utf8_encoding()

from loguru import logger

from zquant.scheduler.job.base import BaseSyncJob
from zquant.services.partition_manager import PartitionManager
from zquant.models.scheduler import TaskExecution

__job_name__ = "sync_factor_columns"


class SyncFactorColumnsJob(BaseSyncJob):
    """同步因子分表列结构任务"""

    def __init__(self):
        super().__init__(__job_name__, "因子分表列同步任务")

    def create_parser(self) -> argparse.ArgumentParser:
        # 列同步任务不需要额外参数
        parser = argparse.ArgumentParser(description=self.description)
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
        self.print_start_info()

        with self.db_session() as db:
            # 获取执行记录（用于进度更新）
            execution = self.get_execution(db)

            logger.info("开始同步因子分表列结构...")

            try:
                result = PartitionManager.sync_spacex_factor_columns(db, execution=execution)

                logger.info(
                    f"列同步完成: "
                    f"处理 {result['tables_processed']} 个表，"
                    f"发现 {result['columns_found']} 个唯一列，"
                    f"添加 {result['columns_added']} 个列"
                )
                
                # 显示详细信息
                if result.get('details'):
                    tables_with_additions = [d for d in result['details'] if d['columns_added'] > 0]
                    if tables_with_additions:
                        logger.info("以下表新增了列:")
                        for detail in tables_with_additions[:10]:  # 只显示前10个
                            logger.info(f"  - {detail['table']}: 新增 {detail['columns_added']} 个列")
                        
                        if len(tables_with_additions) > 10:
                            logger.info(f"  ... 还有 {len(tables_with_additions) - 10} 个表")
                
                self.print_end_info(
                    处理表数=str(result['tables_processed']),
                    添加列数=str(result['columns_added'])
                )
                
                return 0
                
            except Exception as e:
                logger.error(f"因子分表列同步失败: {e}")
                import traceback
                traceback.print_exc()
                return 1


def main():
    job = SyncFactorColumnsJob()
    sys.exit(job.run())


if __name__ == "__main__":
    main()
