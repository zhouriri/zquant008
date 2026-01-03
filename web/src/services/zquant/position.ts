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
// distributed under the Apache License is distributed on an "AS IS" BASIS,
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
 * 查询持仓列表
 * POST /api/v1/positions/query
 */
export async function getPositions(params: {
  code?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
  order_by?: string;
  order?: string;
}) {
  return request<ZQuant.PositionListResponse>('/api/v1/positions/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params,
  });
}

/**
 * 创建持仓
 * POST /api/v1/positions
 */
export async function createPosition(body: ZQuant.PositionCreate) {
  return request<ZQuant.PositionResponse>('/api/v1/positions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 查询单个持仓详情
 * POST /api/v1/positions/get
 */
export async function getPositionById(id: number) {
  return request<ZQuant.PositionResponse>('/api/v1/positions/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { position_id: id },
  });
}

/**
 * 更新持仓
 * POST /api/v1/positions/update
 */
export async function updatePosition(id: number, body: ZQuant.PositionUpdate) {
  return request<ZQuant.PositionResponse>('/api/v1/positions/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, position_id: id },
  });
}

/**
 * 删除持仓
 * POST /api/v1/positions/delete
 */
export async function deletePosition(id: number) {
  return request('/api/v1/positions/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { position_id: id },
  });
}

