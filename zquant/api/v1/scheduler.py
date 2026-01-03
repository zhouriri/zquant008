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
定时任务管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from zquant.api.deps import get_current_active_user
from zquant.core.exceptions import NotFoundError
from zquant.core.permissions import is_admin
from zquant.database import get_db
from zquant.models.scheduler import TaskType
from zquant.models.user import User
from zquant.schemas.scheduler import (
    ExecutionListRequest,
    ExecutionListResponse,
    ExecutionPauseRequest,
    ExecutionResponse,
    ExecutionResumeRequest,
    ExecutionTerminateRequest,
    TaskCreate,
    TaskDeleteRequest,
    TaskDisableRequest,
    TaskEnableRequest,
    TaskExecutionGetRequest,
    TaskExecutionsListRequest,
    TaskGetRequest,
    TaskListRequest,
    TaskListResponse,
    TaskPauseRequest,
    TaskResponse,
    TaskResumeRequest,
    TaskStatsRequest,
    TaskStatsResponse,
    TaskTriggerRequest,
    TaskUpdate,
    TaskWorkflowTasksRequest,
    TaskWorkflowValidateRequest,
    WorkflowTaskConfig,
)
from zquant.services.scheduler import SchedulerService

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="创建定时任务")
def create_task(
    task_data: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """创建定时任务（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 验证手动任务配置
        if task_data.task_type == TaskType.MANUAL_TASK:
            if task_data.cron_expression:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手动任务不支持 Cron 表达式调度")
            if task_data.interval_seconds:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手动任务不支持间隔调度")
        
        # 如果是编排任务，验证配置
        if task_data.task_type == TaskType.WORKFLOW and task_data.config:
            is_valid, error_msg = SchedulerService.validate_workflow_config(db, task_data.config)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"编排任务配置无效: {error_msg}")

        task = SchedulerService.create_task(
            db=db,
            name=task_data.name,
            task_type=task_data.task_type,
            cron_expression=task_data.cron_expression,
            interval_seconds=task_data.interval_seconds,
            description=task_data.description,
            config=task_data.config,
            max_retries=task_data.max_retries,
            retry_interval=task_data.retry_interval,
            enabled=task_data.enabled,
            created_by=current_user.username,
        )
        return TaskResponse.from_orm(task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")


@router.post("/tasks/query", response_model=TaskListResponse, summary="获取任务列表")
def list_tasks(
    request: TaskListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取任务列表"""
    try:
        tasks = SchedulerService.list_tasks(
            db=db,
            skip=request.skip,
            limit=request.limit,
            task_type=request.task_type,
            enabled=request.enabled,
            order_by=request.order_by,
            order=request.order,
        )
        total = len(tasks)  # 简化处理，实际应该查询总数
        task_responses = [TaskResponse.from_orm(task) for task in tasks]
        return TaskListResponse(tasks=task_responses, total=total)
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")


@router.post("/tasks/get", response_model=TaskResponse, summary="获取任务详情")
def get_task(request: TaskGetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """获取任务详情"""
    try:
        task = SchedulerService.get_task(db, request.task_id)
        return TaskResponse.from_orm(task)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")


@router.post("/tasks/update", response_model=TaskResponse, summary="更新任务")
def update_task(
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新任务（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 如果是编排任务且更新了配置，验证配置
        existing_task = SchedulerService.get_task(db, task_data.task_id)
        
        # 验证手动任务配置
        if existing_task.task_type == TaskType.MANUAL_TASK:
            if task_data.cron_expression is not None and task_data.cron_expression:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手动任务不支持 Cron 表达式调度")
            if task_data.interval_seconds is not None and task_data.interval_seconds:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手动任务不支持间隔调度")
        
        if existing_task.task_type == TaskType.WORKFLOW and task_data.config:
            is_valid, error_msg = SchedulerService.validate_workflow_config(db, task_data.config)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"编排任务配置无效: {error_msg}")

        task = SchedulerService.update_task(
            db=db,
            task_id=task_data.task_id,
            name=task_data.name,
            cron_expression=task_data.cron_expression,
            interval_seconds=task_data.interval_seconds,
            description=task_data.description,
            config=task_data.config,
            max_retries=task_data.max_retries,
            retry_interval=task_data.retry_interval,
            updated_by=current_user.username,
        )
        return TaskResponse.from_orm(task)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新任务失败")


@router.post("/tasks/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除任务")
def delete_task(request: TaskDeleteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """删除任务（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        SchedulerService.delete_task(db, request.task_id)
        return
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除任务失败")


@router.post("/tasks/trigger", summary="手动触发任务")
def trigger_task(request: TaskTriggerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """手动触发任务执行"""
    try:
        success = SchedulerService.trigger_task(db, request.task_id)
        if success:
            return {"message": "任务已触发"}
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="触发任务失败")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"触发任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="触发任务失败")


@router.post("/tasks/enable", response_model=TaskResponse, summary="启用任务")
def enable_task(request: TaskEnableRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """启用任务"""
    try:
        task = SchedulerService.enable_task(db, request.task_id)
        return TaskResponse.from_orm(task)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"启用任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="启用任务失败")


@router.post("/tasks/disable", response_model=TaskResponse, summary="禁用任务")
def disable_task(request: TaskDisableRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """禁用任务"""
    try:
        task = SchedulerService.disable_task(db, request.task_id)
        return TaskResponse.from_orm(task)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"禁用任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="禁用任务失败")


@router.post("/tasks/pause", response_model=TaskResponse, summary="暂停任务")
def pause_task(request: TaskPauseRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """暂停任务"""
    try:
        task = SchedulerService.pause_task(db, request.task_id)
        return TaskResponse.from_orm(task)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="暂停任务失败")


@router.post("/tasks/resume", response_model=TaskResponse, summary="恢复任务")
def resume_task(request: TaskResumeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """恢复任务"""
    try:
        task = SchedulerService.resume_task(db, request.task_id)
        return TaskResponse.from_orm(task)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="恢复任务失败")


@router.post("/tasks/executions/list", response_model=ExecutionListResponse, summary="获取任务执行历史")
def get_executions(
    request: TaskExecutionsListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取任务执行历史"""
    try:
        # 验证任务存在
        SchedulerService.get_task(db, request.task_id)

        executions = SchedulerService.get_executions(db, request.task_id, request.skip, request.limit)
        total = len(executions)  # 简化处理
        execution_responses = [ExecutionResponse.from_orm(e) for e in executions]
        return ExecutionListResponse(executions=execution_responses, total=total)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取执行历史失败")


@router.post("/tasks/executions/get", response_model=ExecutionResponse, summary="获取单个执行记录")
def get_execution(
    request: TaskExecutionGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取单个执行记录详情"""
    try:
        # 验证任务存在
        SchedulerService.get_task(db, request.task_id)

        execution = SchedulerService.get_execution(db, request.task_id, request.execution_id)
        return ExecutionResponse.from_orm(execution)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取执行记录失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取执行记录失败")


@router.post("/executions/pause", response_model=ExecutionResponse, summary="暂停执行记录")
def pause_execution(
    request: ExecutionPauseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """暂停执行中的任务记录（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        execution = SchedulerService.pause_execution(db, request.execution_id)
        return ExecutionResponse.from_orm(execution)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"暂停执行记录失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="暂停执行记录失败")


@router.post("/executions/resume", response_model=ExecutionResponse, summary="恢复执行记录")
def resume_execution(
    request: ExecutionResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """恢复已暂停的任务执行记录（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        execution = SchedulerService.resume_execution(db, request.execution_id)
        return ExecutionResponse.from_orm(execution)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"恢复执行记录失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="恢复执行记录失败")


@router.post("/executions/terminate", response_model=ExecutionResponse, summary="终止执行记录")
def terminate_execution(
    request: ExecutionTerminateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """请求终止执行中的任务记录（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        execution = SchedulerService.terminate_execution(db, request.execution_id)
        return ExecutionResponse.from_orm(execution)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"终止执行记录失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="终止执行记录失败")


@router.post("/tasks/workflow/tasks", response_model=list[TaskResponse], summary="获取编排任务中的任务列表")
def get_workflow_tasks(
    request: TaskWorkflowTasksRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """获取编排任务中包含的所有任务"""
    try:
        tasks = SchedulerService.get_workflow_tasks(db, request.task_id)
        return [TaskResponse.from_orm(task) for task in tasks]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"获取编排任务列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取编排任务列表失败")


@router.post("/tasks/workflow/validate", summary="验证编排任务配置")
def validate_workflow_config(
    request: TaskWorkflowValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """验证编排任务配置"""
    try:
        config_dict = request.config.model_dump()
        is_valid, error_msg = SchedulerService.validate_workflow_config(db, config_dict)
        if is_valid:
            return {"valid": True, "message": "配置有效"}
        return {"valid": False, "message": error_msg}
    except Exception as e:
        logger.error(f"验证配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="验证配置失败")


@router.post("/stats", response_model=TaskStatsResponse, summary="获取任务统计信息")
def get_stats(
    request: TaskStatsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取任务统计信息"""
    try:
        stats = SchedulerService.get_stats(db, request.task_id)
        return stats
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取统计信息失败")
