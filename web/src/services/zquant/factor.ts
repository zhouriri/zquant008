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

import { request } from '@umijs/max';

/**
 * 获取因子定义列表
 * POST /api/v1/factor/definitions/query
 */
export async function getFactorDefinitions(params?: {
  skip?: number;
  limit?: number;
  enabled?: boolean;
  order_by?: string;
  order?: string;
}) {
  return request<ZQuant.FactorDefinitionListResponse>('/api/v1/factor/definitions/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 创建因子定义
 * POST /api/v1/factor/definitions
 */
export async function createFactorDefinition(body: ZQuant.FactorDefinitionCreate) {
  return request<ZQuant.FactorDefinitionResponse>('/api/v1/factor/definitions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 更新因子定义
 * POST /api/v1/factor/definitions/update
 */
export async function updateFactorDefinition(id: number, body: ZQuant.FactorDefinitionUpdate) {
  return request<ZQuant.FactorDefinitionResponse>('/api/v1/factor/definitions/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, factor_id: id },
  });
}

/**
 * 删除因子定义
 * POST /api/v1/factor/definitions/delete
 */
export async function deleteFactorDefinition(id: number) {
  return request<void>('/api/v1/factor/definitions/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { factor_id: id },
  });
}

/**
 * 获取因子定义详情
 * POST /api/v1/factor/definitions/get
 */
export async function getFactorDefinition(id: number) {
  return request<ZQuant.FactorDefinitionResponse>('/api/v1/factor/definitions/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { factor_id: id },
  });
}

/**
 * 获取因子配置列表
 * POST /api/v1/factor/configs/query
 */
export async function getFactorConfigs(params?: {
  skip?: number;
  limit?: number;
  enabled?: boolean;
  order_by?: string;
  order?: string;
}) {
  return request<ZQuant.FactorConfigListResponse>('/api/v1/factor/configs/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 获取单个因子配置
 * POST /api/v1/factor/configs/get
 */
export async function getFactorConfigById(factorId: number) {
  return request<ZQuant.FactorConfigResponse>('/api/v1/factor/configs/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { factor_id: factorId },
  });
}

/**
 * 更新因子配置
 * POST /api/v1/factor/configs/update
 */
export async function updateFactorConfigById(
  factorId: number,
  body: {
    mappings?: Array<{
      model_id: number;
      codes: string[] | null;
    }> | null;
    enabled?: boolean | null;
  }
) {
  return request<ZQuant.FactorConfigResponse>('/api/v1/factor/configs/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, factor_id: factorId },
  });
}

/**
 * 删除因子配置
 * POST /api/v1/factor/configs/delete
 */
export async function deleteFactorConfigById(factorId: number) {
  return request<void>('/api/v1/factor/configs/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { factor_id: factorId },
  });
}

/**
 * 获取因子配置（JSON格式）（已废弃，向后兼容）
 * POST /api/v1/factor/definitions/config
 */
export async function getFactorConfig(factorId: number) {
  return request<{
    enabled: boolean;
    mappings: Array<{
      model_id: number;
      codes: string[] | null;
    }>;
  }>('/api/v1/factor/definitions/config', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { factor_id: factorId },
  });
}

/**
 * 更新因子配置（JSON格式）
 * POST /api/v1/factor/definitions/config/update
 */
export async function updateFactorConfigJson(
  factorId: number,
  body: {
    enabled: boolean;
    mappings: Array<{
      model_id: number;
      codes: string[] | null;
    }>;
  }
) {
  return request<{
    enabled: boolean;
    mappings: Array<{
      model_id: number;
      codes: string[] | null;
    }>;
  }>('/api/v1/factor/definitions/config/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, factor_id: factorId },
  });
}

/**
 * 删除因子配置（清空配置）
 * POST /api/v1/factor/definitions/config/delete
 */
export async function deleteFactorConfigJson(factorId: number) {
  return request<void>('/api/v1/factor/definitions/config/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { factor_id: factorId },
  });
}

/**
 * 获取因子模型列表
 * POST /api/v1/factor/models/query
 */
export async function getFactorModels(params?: {
  factor_id?: number;
  skip?: number;
  limit?: number;
  enabled?: boolean;
  order_by?: string;
  order?: string;
}) {
  return request<ZQuant.FactorModelListResponse>('/api/v1/factor/models/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 创建因子模型
 * POST /api/v1/factor/models
 */
export async function createFactorModel(body: ZQuant.FactorModelCreate) {
  return request<ZQuant.FactorModelResponse>('/api/v1/factor/models', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 更新因子模型
 * POST /api/v1/factor/models/update
 */
export async function updateFactorModel(id: number, body: ZQuant.FactorModelUpdate) {
  return request<ZQuant.FactorModelResponse>('/api/v1/factor/models/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, model_id: id },
  });
}

/**
 * 删除因子模型
 * POST /api/v1/factor/models/delete
 */
export async function deleteFactorModel(id: number) {
  return request<void>('/api/v1/factor/models/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { model_id: id },
  });
}

/**
 * 获取因子模型详情
 * POST /api/v1/factor/models/get
 */
export async function getFactorModel(id: number) {
  return request<ZQuant.FactorModelResponse>('/api/v1/factor/models/get', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { model_id: id },
  });
}

/**
 * 创建因子配置
 * POST /api/v1/factor/configs
 */
export async function createFactorConfig(body: ZQuant.FactorConfigCreate) {
  return request<ZQuant.FactorConfigResponse>('/api/v1/factor/configs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 获取因子配置列表（按因子分组）（已废弃）
 * POST /api/v1/factor/configs/grouped
 */
export async function getFactorConfigsGrouped(params?: {
  enabled?: boolean;
}) {
  return request<ZQuant.FactorConfigGroupedListResponse>('/api/v1/factor/configs/grouped', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params || {},
  });
}

/**
 * 更新因子配置（按因子ID，支持多映射）
 * POST /api/v1/factor/configs/by-factor/update
 */
export async function updateFactorConfigByFactor(factorId: number, body: ZQuant.FactorConfigUpdate) {
  return request<ZQuant.FactorConfigGroupedResponse>('/api/v1/factor/configs/by-factor/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, factor_id: factorId },
  });
}

/**
 * 更新单个因子配置
 * POST /api/v1/factor/configs/update_single
 */
export async function updateFactorConfig(id: number, body: ZQuant.FactorConfigSingleUpdate) {
  return request<ZQuant.FactorConfigResponse>('/api/v1/factor/configs/update_single', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { ...body, config_id: id },
  });
}

/**
 * 删除因子配置
 * POST /api/v1/factor/configs/delete_single
 */
export async function deleteFactorConfig(id: number) {
  return request<void>('/api/v1/factor/configs/delete_single', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { config_id: id },
  });
}

/**
 * 删除因子配置（按因子ID，删除该因子的所有配置）
 * POST /api/v1/factor/configs/by-factor/delete
 */
export async function deleteFactorConfigByFactor(factorId: number) {
  return request<void>('/api/v1/factor/configs/by-factor/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: { factor_id: factorId },
  });
}

/**
 * 手动触发因子计算
 * POST /api/v1/factor/calculate
 */
export async function calculateFactor(body: ZQuant.FactorCalculationRequest) {
  return request<ZQuant.FactorCalculationResponse>('/api/v1/factor/calculate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 查询因子计算结果
 * POST /api/v1/factor/results
 */
export async function getFactorResults(body: ZQuant.FactorResultQueryRequest) {
  return request<ZQuant.FactorResultResponse>('/api/v1/factor/results', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

/**
 * 查询量化因子数据
 * POST /api/v1/factor/quant-factors/query
 */
export async function getQuantFactors(params: {
  ts_code?: string;
  start_date?: string;
  end_date?: string;
  filter_conditions?: any;
  skip?: number;
  limit?: number;
  order_by?: string;
  order?: string;
}) {
  return request<ZQuant.QuantFactorQueryResponse>('/api/v1/factor/quant-factors/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: params,
  });
}

