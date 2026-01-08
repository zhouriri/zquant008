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
任务执行器基类
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from zquant.models.scheduler import TaskExecution, TaskStatus, TaskType
from zquant.scheduler.utils import update_execution_progress


class TaskExecutor(ABC):
    """任务执行器基类"""

    @abstractmethod
    def execute(self, db: Session, config: dict[str, Any], execution: Optional[TaskExecution] = None) -> dict[str, Any]:
        """
        执行任务

        Args:
            db: 数据库会话
            config: 任务配置字典
            execution: 执行记录对象（可选），用于更新执行进度

        Returns:
            执行结果字典
        """

    @abstractmethod
    def get_task_type(self) -> TaskType:
        """获取任务类型"""

    def update_progress(
        self,
        db: Session,
        execution: Optional[TaskExecution],
        processed_items: Optional[int] = None,
        total_items: Optional[int] = None,
        current_item: Optional[str] = None,
        progress_percent: Optional[float] = None,
        message: Optional[str] = None,
    ):
        """
        更新执行进度并检查控制标志 (转发到工具函数)
        """
        update_execution_progress(
            db=db,
            execution=execution,
            processed_items=processed_items,
            total_items=total_items,
            current_item=current_item,
            progress_percent=progress_percent,
            message=message,
        )
