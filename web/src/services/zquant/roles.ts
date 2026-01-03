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
 * 查询角色列表
 * POST /api/v1/roles
 */
export async function getRoles(params?: {
  skip?: number;
  limit?: number;
  order_by?: string;
  order?: 'asc' | 'desc';
}) {
  return request<ZQuant.PageResponse<ZQuant.RoleResponse>>('/api/v1/roles', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 查询角色详情
 * POST /api/v1/roles/get
 */
export async function getRole(roleId: number) {
  return request<ZQuant.RoleWithPermissions>('/api/v1/roles/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { role_id: roleId },
  });
}

/**
 * 创建角色
 * POST /api/v1/roles
 */
export async function createRole(body: ZQuant.RoleCreate) {
  return request<ZQuant.RoleResponse>('/api/v1/roles', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 更新角色
 * POST /api/v1/roles/update
 */
export async function updateRole(roleId: number, body: ZQuant.RoleUpdate) {
  return request<ZQuant.RoleResponse>('/api/v1/roles/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, role_id: roleId },
  });
}

/**
 * 删除角色
 * POST /api/v1/roles/delete
 */
export async function deleteRole(roleId: number) {
  return request<{ message: string }>('/api/v1/roles/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { role_id: roleId },
  });
}

/**
 * 查询角色的权限列表
 * POST /api/v1/roles/permissions/list
 */
export async function getRolePermissions(roleId: number) {
  return request<ZQuant.PermissionResponse[]>('/api/v1/roles/permissions/list', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { role_id: roleId },
  });
}

/**
 * 为角色分配权限
 * POST /api/v1/roles/permissions/assign
 */
export async function assignPermissions(roleId: number, body: ZQuant.AssignPermissionsRequest) {
  return request<ZQuant.RoleResponse>('/api/v1/roles/permissions/assign', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, role_id: roleId },
  });
}

/**
 * 为角色添加单个权限
 * POST /api/v1/roles/permissions/add
 */
export async function addPermission(roleId: number, permissionId: number) {
  return request<{ message: string }>('/api/v1/roles/permissions/add', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { role_id: roleId, permission_id: permissionId },
  });
}

/**
 * 移除角色的单个权限
 * POST /api/v1/roles/permissions/remove
 */
export async function removePermission(roleId: number, permissionId: number) {
  return request<{ message: string }>('/api/v1/roles/permissions/remove', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { role_id: roleId, permission_id: permissionId },
  });
}

