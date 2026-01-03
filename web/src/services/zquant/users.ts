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
 * 获取当前用户信息
 * POST /api/v1/users/me
 */
export async function getCurrentUser() {
  return request<ZQuant.UserResponse>('/api/v1/users/me', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: {},
  });
}

/**
 * 创建用户（仅管理员）
 * POST /api/v1/users
 */
export async function createUser(body: ZQuant.UserCreate) {
  return request<ZQuant.UserResponse>('/api/v1/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 获取API密钥列表
 * POST /api/v1/users/me/apikeys
 */
export async function getAPIKeys() {
  return request<ZQuant.APIKeyResponse[]>('/api/v1/users/me/apikeys', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: {},
  });
}

/**
 * 创建API密钥
 * POST /api/v1/users/me/apikeys
 */
export async function createAPIKey(body: ZQuant.APIKeyCreate) {
  return request<ZQuant.APIKeyCreateResponse>('/api/v1/users/me/apikeys', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 删除API密钥
 * POST /api/v1/users/me/apikeys/delete
 */
export async function deleteAPIKey(keyId: number) {
  return request<{ message: string }>('/api/v1/users/me/apikeys/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { key_id: keyId },
  });
}

/**
 * 查询用户列表（分页、筛选）
 * POST /api/v1/users/query
 */
export async function getUsers(params?: {
  skip?: number;
  limit?: number;
  is_active?: boolean;
  role_id?: number;
  username?: string;
  order_by?: string;
  order?: 'asc' | 'desc';
}) {
  return request<ZQuant.PageResponse<ZQuant.UserResponse>>('/api/v1/users/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 查询用户详情
 * POST /api/v1/users/get
 */
export async function getUser(userId: number) {
  return request<ZQuant.UserResponse>('/api/v1/users/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { user_id: userId },
  });
}

/**
 * 更新用户
 * POST /api/v1/users/update
 */
export async function updateUser(userId: number, body: ZQuant.UserUpdate) {
  return request<ZQuant.UserResponse>('/api/v1/users/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, user_id: userId },
  });
}

/**
 * 重置用户密码
 * POST /api/v1/users/reset-password
 */
export async function resetUserPassword(userId: number, body: ZQuant.PasswordReset) {
  return request<{ message: string }>('/api/v1/users/reset-password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, user_id: userId },
  });
}

/**
 * 删除用户
 * POST /api/v1/users/delete
 */
export async function deleteUser(userId: number) {
  return request<{ message: string }>('/api/v1/users/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { user_id: userId },
  });
}

