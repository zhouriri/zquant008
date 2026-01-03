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
定时任务示例脚本

这是一个用于演示定时任务命令执行功能的示例脚本。
脚本会模拟一些数据处理过程，输出执行日志，并返回适当的退出码。

使用方法：
    python scripts/example_scheduled_job.py [--steps N] [--delay SECONDS]

参数：
    --steps N: 处理步骤数量（默认：5）
    --delay SECONDS: 每个步骤的延迟时间（秒，默认：1）
"""

import argparse
from datetime import datetime
import os
from pathlib import Path
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 设置UTF-8编码（Windows系统兼容，作为双重保障）
from zquant.utils.encoding import setup_utf8_encoding

setup_utf8_encoding()

from zquant.database import SessionLocal
from zquant.models.scheduler import TaskExecution
from zquant.scheduler.utils import update_execution_progress


def get_execution(db) -> TaskExecution | None:
    """
    从环境变量获取执行记录ID，并查询数据库获取执行记录对象
    """
    execution_id_str = os.environ.get("ZQUANT_EXECUTION_ID")
    if not execution_id_str:
        return None

    try:
        execution_id = int(execution_id_str)
        execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
        return execution
    except (ValueError, Exception):
        return None


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="定时任务示例脚本")
    parser.add_argument("--steps", type=int, default=5, help="处理步骤数量（默认：5）")
    parser.add_argument("--delay", type=float, default=1.0, help="每个步骤的延迟时间（秒，默认：1）")
    args = parser.parse_args()

    # 输出开始信息
    start_time = datetime.now()
    print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] 示例定时任务开始执行")
    print(f"配置参数: steps={args.steps}, delay={args.delay}秒")
    print("-" * 60)

    db = SessionLocal()
    execution = get_execution(db)

    try:
        # 模拟处理步骤
        processed_items = []
        for i in range(1, args.steps + 1):
            # 更新进度
            update_execution_progress(
                db,
                execution,
                total_items=args.steps,
                processed_items=i - 1,
                current_item=f"step_{i}",
                message=f"正在执行步骤 {i}/{args.steps}...",
            )

            # 模拟处理过程
            print(f"[步骤 {i}/{args.steps}] 正在处理数据...")
            time.sleep(args.delay)

            # 模拟处理结果
            item = {"id": i, "data": f"processed_item_{i}", "timestamp": datetime.now().isoformat()}
            processed_items.append(item)
            print(f"[步骤 {i}/{args.steps}] 处理完成: {item['data']}")

        # 完成更新
        update_execution_progress(db, execution, processed_items=args.steps, message="示例定时任务执行完成")

        # 输出处理结果摘要
        print("-" * 60)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] 示例定时任务执行完成")
        print("执行摘要:")
        print(f"  - 总步骤数: {args.steps}")
        print(f"  - 处理项数: {len(processed_items)}")
        print(f"  - 执行时长: {duration:.2f} 秒")
        print("  - 状态: 成功")

        # 返回成功退出码
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n[警告] 任务被用户中断")
        sys.exit(130)  # 130 表示被 Ctrl+C 中断

    except Exception as e:
        print(f"\n[错误] 任务执行失败: {e!s}")
        if "Task terminated" in str(e):
            sys.exit(130)
        sys.exit(1)  # 1 表示执行失败
    finally:
        db.close()


if __name__ == "__main__":
    main()
