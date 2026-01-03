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

import React, { useState, useEffect, useRef } from 'react';
import { message, Form, Input, DatePicker, Button } from 'antd';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import dayjs from 'dayjs';

import { getQuantFactors, getFactorDefinitions } from '@/services/zquant/factor';
import { renderDate, renderNumber } from '@/components/DataTable';
import { validateTsCodes, getTsCodeValidationError } from '@/utils/tsCodeValidator';

const QuantFactors: React.FC = () => {
  const [form] = Form.useForm();
  const actionRef = useRef<ActionType>(null);
  const [loading, setLoading] = useState(false);
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [factorDefs, setFactorDefs] = useState<Record<string, string>>({});
  const [dynamicColumns, setDynamicColumns] = useState<ProColumns<any>[]>([]);

  // 获取因子定义，用于列名映射
  useEffect(() => {
    const fetchDefs = async () => {
      try {
        const response = await getFactorDefinitions({ limit: 1000 });
        const defMap: Record<string, string> = {};
        response.items.forEach((item: ZQuant.FactorDefinitionResponse) => {
          if (item.column_name) {
            defMap[item.column_name] = item.cn_name || item.factor_name;
          }
        });
        setFactorDefs(defMap);
      } catch (error) {
        console.error('获取因子定义失败:', error);
      }
    };
    fetchDefs();
  }, []);

  // 基础列定义
  const baseColumns: ProColumns<any>[] = [
    {
      title: 'TS代码',
      dataIndex: 'ts_code',
      width: 100,
      fixed: 'left',
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      width: 100,
      fixed: 'left',
      render: (text) => text || '-',
    },
    {
      title: '交易日期',
      dataIndex: 'trade_date',
      width: 110,
      fixed: 'left',
      render: (_, record) => renderDate(record.trade_date),
    },
  ];

  const handleQuery = async () => {
    try {
      await form.validateFields();
      actionRef.current?.reload();
    } catch (error: any) {
      if (error?.errorFields) {
        return;
      }
      message.error('查询失败');
    }
  };

  return (
    <div>
      <Form
        form={form}
        layout="inline"
        onFinish={handleQuery}
        initialValues={{
          ts_code: '000001.SZ',
          start_date: dayjs().subtract(1, 'month'),
          end_date: dayjs(),
        }}
        style={{ marginBottom: 16, padding: 16, background: '#fff' }}
      >
        <Form.Item name="ts_code" label="TS代码" rules={[{ required: true, message: '请输入TS代码' }]}>
          <Input placeholder="例如：000001.SZ" style={{ width: 200 }} />
        </Form.Item>
        <Form.Item name="start_date" label="开始日期">
          <DatePicker style={{ width: 150 }} />
        </Form.Item>
        <Form.Item name="end_date" label="结束日期">
          <DatePicker style={{ width: 150 }} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">
            查询
          </Button>
        </Form.Item>
      </Form>

      <ProTable<any>
        headerTitle="量化因子结果"
        actionRef={actionRef}
        rowKey={(record) => `${record.ts_code}_${record.trade_date}`}
        search={false}
        loading={loading}
        request={async () => {
          const values = form.getFieldsValue();
          if (!values.ts_code) {
            return { data: [], success: true, total: 0 };
          }

          setLoading(true);
          try {
            const { ts_code, start_date, end_date } = values;
            
            const formattedStartDate = start_date ? dayjs(start_date).format('YYYY-MM-DD') : undefined;
            const formattedEndDate = end_date ? dayjs(end_date).format('YYYY-MM-DD') : undefined;

            // 验证 TS 代码
            const validation = validateTsCodes(ts_code);
            if (!validation.valid) {
              message.error(getTsCodeValidationError(validation.invalidCodes));
              return { data: [], success: false, total: 0 };
            }

            const response = await getQuantFactors({
              ts_code,
              start_date: formattedStartDate,
              end_date: formattedEndDate,
              skip: 0,
              limit: 100, // 初始加载 100 条
              order_by: 'trade_date',
              order: 'desc',
            });

            setDataSource(response.items);
            setTotal(response.total);

            // 根据返回的数据动态生成因子列
            if (response.items.length > 0) {
              const firstItem = response.items[0];
              const excludeKeys = ['id', 'ts_code', 'trade_date', 'stock_name', 'total_count', 'created_by', 'created_time', 'updated_by', 'updated_time'];
              
              const newDynamicCols: ProColumns<any>[] = Object.keys(firstItem)
                .filter(key => !excludeKeys.includes(key))
                .map(key => ({
                  title: factorDefs[key] || key,
                  dataIndex: key,
                  width: 120,
                  sorter: true,
                  render: (val) => typeof val === 'number' ? renderNumber(val) : val,
                }));
              
              setDynamicColumns(newDynamicCols);
            }

            return {
              data: response.items,
              success: true,
              total: response.total,
            };
          } catch (error: any) {
            message.error(`查询量化因子失败: ${error.message || '未知错误'}`);
            return { data: [], success: false, total: 0 };
          } finally {
            setLoading(false);
          }
        }}
        columns={[...baseColumns, ...dynamicColumns]}
        scroll={{ x: Math.max(1000, 310 + dynamicColumns.length * 120) }}
        pagination={{
          defaultPageSize: 20,
          showSizeChanger: true,
        }}
      />
    </div>
  );
};

export default QuantFactors;
