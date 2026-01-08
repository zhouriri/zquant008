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
定时任务相关的Pydantic Schema
"""

from datetime import datetime
from typing import Any, List, Dict, Optional

from pydantic import BaseModel, Field

from zquant.models.scheduler import TaskScheduleStatus, TaskStatus, TaskType
from zquant.schemas.common import QueryRequest


class TaskCreate(BaseModel):
    """创建任务请求"""

    name: str = Field(..., description="任务名称")
    task_type: TaskType = Field(..., description="任务类型")
    cron_expression: Optional[str] = Field(None, description="Cron表达式（如：0 18 * * *）")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    description: Optional[str] = Field(None, description="任务描述")
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="任务配置（JSON格式）。支持命令执行配置：command（执行命令/脚本，如：python instock/cron/example_scheduled_job.py），timeout_seconds（超时时间，可选，默认3600秒）",
    )
    max_retries: int = Field(3, description="最大重试次数")
    retry_interval: int = Field(60, description="重试间隔（秒）")
    enabled: bool = Field(True, description="是否启用")


class TaskUpdate(BaseModel):
    """更新任务请求模型"""

    task_id: int = Field(..., description="任务ID")
    name: Optional[str] = Field(None, description="任务名称")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    description: Optional[str] = Field(None, description="任务描述")
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="任务配置（JSON格式）。支持命令执行配置：command（执行命令/脚本，如：python instock/cron/example_scheduled_job.py），timeout_seconds（超时时间，可选，默认3600秒）",
    )
    max_retries: Optional[int] = Field(None, description="最大重试次数")
    retry_interval: Optional[int] = Field(None, description="重试间隔（秒）")


class TaskGetRequest(BaseModel):
    """获取任务详情请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskDeleteRequest(BaseModel):
    """删除任务请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskTriggerRequest(BaseModel):
    """手动触发任务请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskEnableRequest(BaseModel):
    """启用任务请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskDisableRequest(BaseModel):
    """禁用任务请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskPauseRequest(BaseModel):
    """暂停任务请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskResumeRequest(BaseModel):
    """恢复任务请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskExecutionsListRequest(QueryRequest):
    """获取任务执行历史列表请求模型"""
    task_id: int = Field(..., description="任务ID")


class TaskExecutionGetRequest(BaseModel):
    """获取单个执行记录详情请求模型"""
    task_id: int = Field(..., description="任务ID")
    execution_id: int = Field(..., description="执行记录ID")


class ExecutionPauseRequest(BaseModel):
    """暂停执行请求模型"""
    execution_id: int = Field(..., description="执行记录ID")


class ExecutionResumeRequest(BaseModel):
    """恢复执行请求模型"""
    execution_id: int = Field(..., description="执行记录ID")


class ExecutionTerminateRequest(BaseModel):
    """终止执行请求模型"""
    execution_id: int = Field(..., description="执行记录ID")


class TaskWorkflowTasksRequest(BaseModel):
    """获取编排任务中的子任务列表请求模型"""
    task_id: int = Field(..., description="编排任务ID")


class WorkflowTaskItem(BaseModel):
    """编排任务中的单个任务项"""

    task_id: int = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    dependencies: List[int] = Field(default_factory=list, description="依赖的任务ID列表")


class WorkflowTaskConfig(BaseModel):
    """编排任务配置"""

    workflow_type: str = Field(..., description="执行模式：serial（串行）或 parallel（并行）")
    tasks: List[WorkflowTaskItem] = Field(..., description="任务列表")
    on_failure: str = Field("stop", description="失败处理策略：stop（停止）或 continue（继续）")


class TaskWorkflowValidateRequest(BaseModel):
    """验证编排任务配置请求模型"""
    task_id: int = Field(..., description="任务ID")
    config: WorkflowTaskConfig = Field(..., description="配置内容")


class TaskResponse(BaseModel):
    """任务响应"""

    id: int = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    job_id: str = Field(..., description="调度器任务ID")
    task_type: TaskType = Field(..., description="任务类型：manual_task, common_task, workflow")
    cron_expression: Optional[str] = Field(None, description="Cron表达式（如：0 18 * * *）")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    enabled: bool = Field(..., description="是否启用")
    paused: bool = Field(..., description="是否暂停")
    description: Optional[str] = Field(None, description="任务描述")
    config: dict[str, Any] = Field(default_factory=dict, description="任务配置（JSON格式）")
    max_retries: int = Field(..., description="最大重试次数")
    retry_interval: int = Field(..., description="重试间隔（秒）")
    created_by: Optional[str] = Field(None, description="创建人")
    created_time: datetime = Field(..., description="创建时间")
    updated_by: Optional[str] = Field(None, description="修改人")
    updated_time: datetime = Field(..., description="更新时间")
    latest_execution_time: Optional[datetime] = Field(None, description="最新执行时间")
    latest_execution_status: Optional[TaskStatus] = Field(None, description="最新执行状态")
    latest_execution_current_item: Optional[str] = Field(None, description="最新执行当前处理数据")
    latest_execution_progress: Optional[float] = Field(None, description="最新执行进度百分比")
    schedule_status: Optional[TaskScheduleStatus] = Field(None, description="调度状态")

    @classmethod
    def from_orm(cls, obj):
        """从ORM对象创建响应对象"""
        data = {
            "id": obj.id,
            "name": obj.name,
            "job_id": obj.job_id,
            "task_type": obj.task_type,
            "cron_expression": obj.cron_expression,
            "interval_seconds": obj.interval_seconds,
            "enabled": obj.enabled,
            "paused": getattr(obj, "paused", False),
            "description": obj.description,
            "config": obj.get_config(),
            "max_retries": obj.max_retries,
            "retry_interval": obj.retry_interval,
            "created_by": getattr(obj, "created_by", None),
            "created_time": obj.created_time,
            "updated_by": getattr(obj, "updated_by", None),
            "updated_time": obj.updated_time,
            "latest_execution_time": getattr(obj, "latest_execution_time", None),
            "latest_execution_status": getattr(obj, "latest_execution_status", None),
            "latest_execution_current_item": getattr(obj, "latest_execution_current_item", None),
            "latest_execution_progress": getattr(obj, "latest_execution_progress", None),
            "schedule_status": getattr(obj, "schedule_status", None),
        }
        return cls(**data)

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """任务执行历史响应"""

    id: int = Field(..., description="执行记录ID")
    task_id: int = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="执行状态：pending, running, success, failed, paused")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行耗时（秒）")
    result: dict[str, Any] = Field(default_factory=dict, description="执行结果（JSON格式）")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(..., description="重试次数")
    progress_percent: float = Field(0.0, description="进度百分比")
    current_item: Optional[str] = Field(None, description="当前处理数据")
    total_items: int = Field(0, description="总项数")
    processed_items: int = Field(0, description="已处理项数")
    estimated_end_time: Optional[datetime] = Field(None, description="预计结束时间")
    is_paused: bool = Field(False, description="是否已暂停")
    terminate_requested: bool = Field(False, description="是否已请求终止")
    created_by: Optional[str] = Field(None, description="创建人")
    created_time: datetime = Field(..., description="创建时间")
    updated_by: Optional[str] = Field(None, description="修改人")
    updated_time: Optional[datetime] = Field(None, description="更新时间")

    @classmethod
    def from_orm(cls, obj):
        """从ORM对象创建响应对象"""
        data = {
            "id": obj.id,
            "task_id": obj.task_id,
            "status": obj.status,
            "start_time": obj.start_time,
            "end_time": obj.end_time,
            "duration_seconds": obj.duration_seconds,
            "result": obj.get_result(),
            "error_message": obj.error_message,
            "retry_count": obj.retry_count,
            "progress_percent": getattr(obj, "progress_percent", 0.0),
            "current_item": getattr(obj, "current_item", None),
            "total_items": getattr(obj, "total_items", 0),
            "processed_items": getattr(obj, "processed_items", 0),
            "estimated_end_time": getattr(obj, "estimated_end_time", None),
            "is_paused": getattr(obj, "is_paused", False),
            "terminate_requested": getattr(obj, "terminate_requested", False),
            "created_by": getattr(obj, "created_by", None),
            "created_time": obj.created_time,
            "updated_by": getattr(obj, "updated_by", None),
            "updated_time": getattr(obj, "updated_time", None),
        }
        return cls(**data)

    class Config:
        from_attributes = True


class TaskStatsResponse(BaseModel):
    """任务统计响应"""

    total_executions: int = Field(..., description="总执行次数")
    success_count: int = Field(..., description="成功次数")
    failed_count: int = Field(..., description="失败次数")
    running_count: int = Field(..., description="运行中次数")
    success_rate: float = Field(..., description="成功率（0-1之间的小数）")
    avg_duration_seconds: float = Field(..., description="平均执行时长（秒）")
    latest_execution_time: Optional[str] = Field(None, description="最近执行时间（ISO格式）")


class TaskListRequest(QueryRequest):
    """任务列表查询请求模型"""
    task_type: Optional[TaskType] = Field(None, description="任务类型")
    enabled: Optional[bool] = Field(None, description="是否启用")
    order_by: Optional[str] = Field(
        None, description="排序字段：id, name, task_type, enabled, paused, max_retries, created_time, updated_time"
    )


class TaskListResponse(BaseModel):
    """任务列表响应"""

    tasks: List[TaskResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总记录数")


class ExecutionListRequest(QueryRequest):
    """执行历史列表查询请求模型"""
    pass


class TaskStatsRequest(BaseModel):
    """任务统计查询请求模型"""
    task_id: Optional[int] = Field(None, description="任务ID（可选）")


class ExecutionListResponse(BaseModel):
    """执行历史列表响应"""

    executions: List[ExecutionResponse] = Field(..., description="执行记录列表")
    total: int = Field(..., description="总记录数")
