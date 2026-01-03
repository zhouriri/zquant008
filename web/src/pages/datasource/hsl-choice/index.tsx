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

import { PlusOutlined } from '@ant-design/icons';
import {
    ActionType,
    ModalForm,
    ProColumns,
    ProFormDatePicker,
    ProFormTextArea,
    ProTable,
} from '@ant-design/pro-components';
import { Button, message, Tag } from 'antd';
import dayjs from 'dayjs';
import React, { useRef, useState } from 'react';
import { addHslChoice, queryHslChoice } from '@/services/zquant/hslChoice';
import { renderDateTime } from '@/components/DataTable';

const HslChoice: React.FC = () => {
    const actionRef = useRef<ActionType>();
    const [createModalVisible, setCreateModalVisible] = useState<boolean>(false);

    const columns: ProColumns<any>[] = [
        {
            title: '开始日期',
            dataIndex: 'start_date',
            valueType: 'date',
            hideInTable: true,
            initialValue: dayjs().subtract(1, 'month'),
        },
        {
            title: '结束日期',
            dataIndex: 'end_date',
            valueType: 'date',
            hideInTable: true,
            initialValue: dayjs(),
        },
        {
            title: '交易日期',
            dataIndex: 'trade_date',
            width: 120,
            search: false,
            sorter: (a, b) => dayjs(a.trade_date).unix() - dayjs(b.trade_date).unix(),
        },
        {
            title: 'TS代码',
            dataIndex: 'ts_code',
            width: 120,
        },
        {
            title: '股票代码',
            dataIndex: 'code',
            width: 100,
        },
        {
            title: '股票名称',
            dataIndex: 'name',
            width: 120,
        },
        {
            title: '创建人',
            dataIndex: 'created_by',
            width: 100,
            search: false,
        },
        {
            title: '创建时间',
            dataIndex: 'created_time',
            width: 160,
            search: false,
            render: (val) => renderDateTime(val),
        },
        {
            title: '修改人',
            dataIndex: 'updated_by',
            width: 100,
            search: false,
        },
        {
            title: '修改时间',
            dataIndex: 'updated_time',
            width: 160,
            search: false,
            render: (val) => renderDateTime(val),
        },
    ];

    const handleAdd = async (values: any) => {
        try {
            // 处理 ts_codes
            const codes = values.ts_codes
                .split(/[\n,，\s]+/)
                .map((code: string) => code.trim())
                .filter((code: string) => code);

            if (codes.length === 0) {
                message.warning('请输入有效股票代码');
                return false;
            }

            await addHslChoice({
                trade_date: values.trade_date,
                ts_codes: codes,
            });

            message.success('添加成功');
            setCreateModalVisible(false);
            actionRef.current?.reload();
            return true;
        } catch (error: any) {
            message.error('添加失败: ' + (error?.response?.data?.detail || error.message));
            return false;
        }
    };

    return (
        <>
            <ProTable<any>
                actionRef={actionRef}
                rowKey="id"
                search={{
                    labelWidth: 120,
                }}
                toolBarRender={() => [
                    <Button
                        type="primary"
                        key="primary"
                        onClick={() => {
                            setCreateModalVisible(true);
                        }}
                    >
                        <PlusOutlined /> 新增
                    </Button>,
                ]}
                request={async (params, sort, filter) => {
                    const res = await queryHslChoice({
                        ...params,
                        page: params.current,
                        page_size: params.pageSize,
                    });
                    return {
                        data: res.items,
                        success: true,
                        total: res.total,
                    };
                }}
                columns={columns}
            />
            <ModalForm
                title="新增ZQ精选数据"
                visible={createModalVisible}
                onVisibleChange={setCreateModalVisible}
                onFinish={handleAdd}
                width={500}
            >
                <ProFormDatePicker
                    name="trade_date"
                    label="交易日期"
                    rules={[{ required: true, message: '请选择交易日期' }]}
                    initialValue={dayjs()}
                />
                <ProFormTextArea
                    name="ts_codes"
                    label="TS代码"
                    placeholder="请输入TS代码（如 000001.SZ），支持输入多个，请用换行、逗号或空格分隔"
                    rules={[{ required: true, message: '请输入TS代码' }]}
                    fieldProps={{
                        rows: 10,
                    }}
                />
            </ModalForm>
        </>
    );
};

export default HslChoice;
