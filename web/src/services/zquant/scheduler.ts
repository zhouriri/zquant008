// @ts-ignore
// Copyright 2025 ZQuant Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Author: kevin
// Contact:
//     - Email: kevin@vip.qq.com
//     - Wechat: zquant2025
//     - Issues: https://github.com/yoyoung/zquant/issues
//     - Documentation: https://github.com/yoyoung/zquant/blob/main/README.md
//     - Repository: https://github.com/yoyoung/zquant

/* eslint-disable */
import { request } from '@umijs/max';

/**
 * 创建定时任务
 * POST /api/v1/scheduler/tasks
 */
export async function createTask(body: ZQuant.TaskCreate) {
  return request<ZQuant.TaskResponse>('/api/v1/scheduler/tasks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 获取任务列表
 * POST /api/v1/scheduler/tasks/query
 */
export async function getTasks(params?: {
  skip?: number;
  limit?: number;
  task_type?: string;
  enabled?: boolean;
  order_by?: string;
  order?: 'asc' | 'desc';
}) {
  return request<ZQuant.TaskListResponse>('/api/v1/scheduler/tasks/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 获取任务详情
 * POST /api/v1/scheduler/tasks/get
 */
export async function getTask(id: number) {
  return request<ZQuant.TaskResponse>('/api/v1/scheduler/tasks/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: id },
  });
}

/**
 * 更新任务
 * POST /api/v1/scheduler/tasks/update
 */
export async function updateTask(id: number, body: ZQuant.TaskUpdate) {
  return request<ZQuant.TaskResponse>('/api/v1/scheduler/tasks/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, task_id: id },
  });
}

/**
 * 删除任务
 * POST /api/v1/scheduler/tasks/delete
 */
export async function deleteTask(id: number) {
  return request('/api/v1/scheduler/tasks/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: id },
  });
}

/**
 * 手动触发任务
 * POST /api/v1/scheduler/tasks/trigger
 */
export async function triggerTask(id: number) {
  return request<{ message: string }>('/api/v1/scheduler/tasks/trigger', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: id },
  });
}

/**
 * 启用任务
 * POST /api/v1/scheduler/tasks/enable
 */
export async function enableTask(id: number) {
  return request<ZQuant.TaskResponse>('/api/v1/scheduler/tasks/enable', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: id },
  });
}

/**
 * 禁用任务
 * POST /api/v1/scheduler/tasks/disable
 */
export async function disableTask(id: number) {
  return request<ZQuant.TaskResponse>('/api/v1/scheduler/tasks/disable', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: id },
  });
}

/**
 * 暂停任务
 * POST /api/v1/scheduler/tasks/pause
 */
export async function pauseTask(id: number) {
  return request<ZQuant.TaskResponse>('/api/v1/scheduler/tasks/pause', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: id },
  });
}

/**
 * 恢复任务
 * POST /api/v1/scheduler/tasks/resume
 */
export async function resumeTask(id: number) {
  return request<ZQuant.TaskResponse>('/api/v1/scheduler/tasks/resume', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: id },
  });
}

/**
 * 获取任务执行历史
 * POST /api/v1/scheduler/tasks/executions/list
 */
export async function getTaskExecutions(id: number, params?: {
  skip?: number;
  limit?: number;
}) {
  return request<ZQuant.ExecutionListResponse>('/api/v1/scheduler/tasks/executions/list', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...params, task_id: id },
  });
}

/**
 * 获取单个执行记录
 * POST /api/v1/scheduler/tasks/executions/get
 */
export async function getExecution(taskId: number, executionId: number) {
  return request<ZQuant.ExecutionResponse>('/api/v1/scheduler/tasks/executions/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: taskId, execution_id: executionId },
  });
}

/**
 * 获取编排任务中的任务列表
 * POST /api/v1/scheduler/tasks/workflow/tasks
 */
export async function getWorkflowTasks(taskId: number) {
  return request<ZQuant.TaskResponse[]>('/api/v1/scheduler/tasks/workflow/tasks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: taskId },
  });
}

/**
 * 验证编排任务配置
 * POST /api/v1/scheduler/tasks/workflow/validate
 */
export async function validateWorkflowConfig(taskId: number, config: ZQuant.WorkflowTaskConfig) {
  return request<{ valid: boolean; message: string }>('/api/v1/scheduler/tasks/workflow/validate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { task_id: taskId, config },
  });
}

/**
 * 暂停任务执行
 * POST /api/v1/scheduler/executions/pause
 */
export async function pauseExecution(executionId: number) {
  return request<ZQuant.ExecutionResponse>('/api/v1/scheduler/executions/pause', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { execution_id: executionId },
  });
}

/**
 * 恢复任务执行
 * POST /api/v1/scheduler/executions/resume
 */
export async function resumeExecution(executionId: number) {
  return request<ZQuant.ExecutionResponse>('/api/v1/scheduler/executions/resume', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { execution_id: executionId },
  });
}

/**
 * 终止任务执行
 * POST /api/v1/scheduler/executions/terminate
 */
export async function terminateExecution(executionId: number) {
  return request<ZQuant.ExecutionResponse>('/api/v1/scheduler/executions/terminate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { execution_id: executionId },
  });
}

/**
 * 获取任务统计信息
 * POST /api/v1/scheduler/stats
 */
export async function getTaskStats(taskId?: number) {
  return request<ZQuant.TaskStatsResponse>('/api/v1/scheduler/stats', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: taskId ? { task_id: taskId } : {},
  });
}

