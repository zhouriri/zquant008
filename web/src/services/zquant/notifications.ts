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
 * 获取通知列表
 * POST /api/v1/notifications/query
 */
export async function getNotifications(params?: {
  skip?: number;
  limit?: number;
  is_read?: boolean;
  type?: ZQuant.NotificationType;
  order_by?: string;
  order?: 'asc' | 'desc';
}) {
  return request<ZQuant.NotificationListResponse>('/api/v1/notifications/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 获取通知统计
 * POST /api/v1/notifications/stats
 */
export async function getNotificationStats() {
  return request<ZQuant.NotificationStatsResponse>('/api/v1/notifications/stats', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: {},
  });
}

/**
 * 获取通知详情
 * POST /api/v1/notifications/get
 */
export async function getNotification(notificationId: number) {
  return request<ZQuant.NotificationResponse>('/api/v1/notifications/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { notification_id: notificationId },
  });
}

/**
 * 标记通知为已读
 * POST /api/v1/notifications/read
 */
export async function markNotificationAsRead(notificationId: number) {
  return request<ZQuant.NotificationResponse>('/api/v1/notifications/read', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { notification_id: notificationId },
  });
}

/**
 * 全部标记为已读
 * POST /api/v1/notifications/read-all
 */
export async function markAllNotificationsAsRead() {
  return request<{ message: string; count: number }>('/api/v1/notifications/read-all', {
    method: 'POST',
  });
}

/**
 * 删除通知
 * POST /api/v1/notifications/delete
 */
export async function deleteNotification(notificationId: number) {
  return request<{ message: string }>('/api/v1/notifications/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { notification_id: notificationId },
  });
}

/**
 * 创建通知（管理员或系统）
 * POST /api/v1/notifications
 */
export async function createNotification(body: ZQuant.NotificationCreate) {
  return request<ZQuant.NotificationResponse>('/api/v1/notifications', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

