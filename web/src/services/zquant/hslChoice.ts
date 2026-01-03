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

import { request } from '@umijs/max';

/** 获取ZQ精选数据 POST /api/v1/hsl-choice */
export async function queryHslChoice(
    params: {
        // query
        start_date?: string;
        end_date?: string;
        ts_code?: string;
        code?: string;
        name?: string;
        /** 当前的页码 */
        page?: number;
        /** 页面的容量 */
        page_size?: number;
    },
    options?: { [key: string]: any },
) {
    return request<ZQuant.Pagination<any>>('/api/v1/hsl-choice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        data: params,
        ...(options || {}),
    });
}

/** 添加ZQ精选数据 POST /api/v1/hsl-choice/add */
export async function addHslChoice(
    body: {
        trade_date: string;
        ts_codes: string[];
    },
    options?: { [key: string]: any },
) {
    return request<any>('/api/v1/hsl-choice/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        data: body,
        ...(options || {}),
    });
}
