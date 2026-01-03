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

import {
    ProForm,
    ProFormDatePicker,
    ProFormInstance,
    ProFormSelect,
    ProFormText,
    ProFormTextArea,
    ProTable,
} from '@ant-design/pro-components';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { Card, message, Space, Button, Modal, Tooltip, Checkbox, Col, Drawer, Row, Typography } from 'antd';
import { LinkOutlined, StarOutlined, SettingOutlined } from '@ant-design/icons';
import React, { useEffect, useRef, useState } from 'react';
import dayjs from 'dayjs';
import { getStrategies, queryStrategyResults, getAvailableColumns } from '@/services/zquant/stockFilter';
import { createFavorite } from '@/services/zquant/favorite';
import { renderDateTime } from '@/components/DataTable';

const UNIT_FACTORS: Record<string, number> = {
    total_mv: 10000, // 万元 -> 亿
    circ_mv: 10000, // 万元 -> 亿
    amount: 100000, // 千元 -> 亿
    total_share: 10000, // 万股 -> 亿股
    float_share: 10000, // 万股 -> 亿股
    free_share: 10000, // 万股 -> 亿股
};

/**
 * 格式化数字显示
 */
const renderNumber = (val: any, fractionDigits: number = 2, field?: string) => {
    if (val === null || val === undefined || typeof val !== 'number') return val;
    let displayValue = val;
    if (field && UNIT_FACTORS[field]) {
        displayValue = val / UNIT_FACTORS[field];
    }
    return displayValue.toLocaleString('zh-CN', {
        minimumFractionDigits: fractionDigits,
        maximumFractionDigits: fractionDigits,
    });
};

const { Text } = Typography;

const StrategyStocks: React.FC = () => {
    const actionRef = useRef<ActionType>(null);
    const searchFormRef = useRef<ProFormInstance>(null);
    const favoriteFormRef = useRef<ProFormInstance>(null);

    const [strategies, setStrategies] = useState<ZQuant.StockFilterStrategyResponse[]>([]);
    // 初始化默认查询参数，确保页面加载时 ProTable 能正常触发 request 并渲染列
    const [queryParams, setQueryParams] = useState<any>({
        trade_date: dayjs().format('YYYY-MM-DD'),
    });
    const [addFavoriteModalVisible, setAddFavoriteModalVisible] = useState(false);
    const [selectedStock, setSelectedStock] = useState<any>(null);
    const [availableColumns, setAvailableColumns] = useState<ZQuant.AvailableColumnsResponse | null>(null);
    const [columnDrawerVisible, setColumnDrawerVisible] = useState(false);

    // 默认展示的核心列
    const DEFAULT_COLUMNS = [
        'ts_code',
        'name',
        'industry',
        'pe',
        'pb',
        'pct_chg',
        'turnover_rate',
        'amount',
        'total_mv',
        'circ_mv',
        'strategy_name'
    ];

    const [selectedColumns, setSelectedColumns] = useState<string[]>(DEFAULT_COLUMNS);

    // 加载策略列表
    useEffect(() => {
        const loadStrategies = async () => {
            try {
                const response = await getStrategies();
                setStrategies(response.items);
            } catch (error: any) {
                message.error('加载策略列表失败');
            }
        };
        loadStrategies();
    }, []);

    // 加载可用列
    useEffect(() => {
        const loadColumns = async () => {
            try {
                const response = await getAvailableColumns();
                setAvailableColumns(response);
            } catch (error: any) {
                message.error('加载可用列失败');
            }
        };
        loadColumns();
    }, []);

    // 构建列定义
    const columns = React.useMemo(() => {
        if (!availableColumns) return [];

    const allAvailableFields = [
        ...availableColumns.basic,
        ...availableColumns.daily_basic,
        ...availableColumns.daily,
        ...(availableColumns.factor || []),
        ...(availableColumns.audit || []),
    ];

        const result: ProColumns<any>[] = [
            {
                title: '交易日期',
                dataIndex: 'trade_date',
                key: 'trade_date',
                width: 100,
                fixed: 'left',
                sorter: true,
                render: (text) => text || queryParams.trade_date,
            }
        ];

        // 遍历所有可用列元数据生成 ProTable 列配置
        allAvailableFields.forEach(col => {
            if (col.field === 'trade_date') return; // 已在上方手动处理

            const isSelected = selectedColumns.includes(col.field);
            
            result.push({
                title: UNIT_FACTORS[col.field] ? `${col.label}(亿)` : col.label,
                dataIndex: col.field,
                key: col.field, // 必须设置 key，否则 ProTable 列设置功能可能失效
                width: col.field === 'strategy_name' ? 150 : 100,
                align: col.type === 'number' ? 'right' : 'left',
                sorter: true,
                hideInTable: !isSelected,
                fixed: ['ts_code', 'name'].includes(col.field) ? 'left' : undefined,
                render: (val) => {
                    if (col.field === 'pct_chg') {
                        if (typeof val !== 'number') return val;
                        const color = val > 0 ? 'red' : val < 0 ? 'green' : 'inherit';
                        return <span style={{ color }}>{val.toFixed(2)}</span>;
                    }
                    if (col.type === 'datetime') {
                        return renderDateTime(val);
                    }
                    if (col.type === 'number') {
                        let digits = 2;
                        if (['macd_dif', 'macd_dea', 'macd'].includes(col.field)) digits = 3;
                        if (col.field === 'adj_factor') digits = 4;
                        if (col.field === 'dd_vol') digits = 0;
                        return renderNumber(val, digits, col.field);
                    }
                    return val;
                }
            });
        });

        // 操作列
        result.push({
            title: '操作',
            key: 'option',
            width: 120,
            fixed: 'right',
            hideInSetting: true, // 操作列不出现在齿轮设置中
            render: (_: any, record: any) => (
                <Space size="small">
                    <Tooltip title="查看百度股市通">
                        <Button
                            type="link"
                            size="small"
                            icon={<LinkOutlined />}
                            onClick={() => handleOpenBaiduStock(record)}
                        />
                    </Tooltip>
                    <Tooltip title="添加自选">
                        <Button
                            type="link"
                            size="small"
                            icon={<StarOutlined />}
                            onClick={() => handleShowAddFavorite(record)}
                        />
                    </Tooltip>
                </Space>
            ),
        });

        return result;
    }, [availableColumns, queryParams.trade_date]);

    const handleOpenBaiduStock = (record: any) => {
        const code = record.ts_code ? record.ts_code.split('.')[0] : '';
        if (code) {
            window.open(`https://gushitong.baidu.com/stock/ab-${code}`, '_blank');
        } else {
            message.warning('股票代码格式不正确');
        }
    };

    const handleShowAddFavorite = (record: any) => {
        setSelectedStock(record);
        setAddFavoriteModalVisible(true);
        setTimeout(() => {
            favoriteFormRef.current?.setFieldsValue({
                code: record.ts_code ? record.ts_code.split('.')[0] : '',
                comment: '',
            });
        }, 100);
    };

    const handleAddToFavorite = async (values: any) => {
        try {
            await createFavorite({
                code: values.code,
                comment: values.comment || '',
                fav_datettime: dayjs().format('YYYY-MM-DD HH:mm:ss'),
            });
            message.success('添加自选成功');
            setAddFavoriteModalVisible(false);
            setSelectedStock(null);
            return true;
        } catch (error: any) {
            message.error(error?.response?.data?.detail || '添加自选失败');
            return false;
        }
    };

    const handleQuery = async () => {
        const values = searchFormRef.current?.getFieldsValue();
        if (!values?.trade_date) {
            message.warning('请选择交易日期');
            return;
        }
        if (!values?.strategy_id) {
            message.warning('请选择量化策略');
            return;
        }

        setQueryParams({
            trade_date: dayjs(values.trade_date).format('YYYY-MM-DD'),
            strategy_id: values.strategy_id,
            _t: Date.now(),
        });
    };

    return (
        <Card>
            <ProForm
                formRef={searchFormRef}
                layout="inline"
                onFinish={handleQuery}
                submitter={{
                    render: (props) => (
                        <Space>
                            <Button type="primary" key="submit" onClick={() => props.form?.submit?.()}>
                                查询
                            </Button>
                        </Space>
                    ),
                }}
            >
                <ProFormDatePicker
                    name="trade_date"
                    label="交易日期"
                    width="sm"
                    initialValue={dayjs()}
                    rules={[{ required: true, message: '请选择交易日期' }]}
                />
                <ProFormSelect
                    name="strategy_id"
                    label="量化策略"
                    width="md"
                    options={strategies.map((s) => ({ label: s.name, value: s.id }))}
                    placeholder="请选择量化策略"
                    rules={[{ required: true, message: '请选择量化策略' }]}
                />
            </ProForm>

            <ProTable<any>
                actionRef={actionRef}
                columns={columns}
                search={false}
                options={{
                    setting: false,
                    fullScreen: true,
                    reload: true,
                }}
                toolBarRender={() => [
                    <Tooltip key="column-settings" title="列设置">
                        <Button
                            type="text"
                            icon={<SettingOutlined />}
                            onClick={() => setColumnDrawerVisible(true)}
                            style={{ fontSize: 16 }}
                        />
                    </Tooltip>,
                ]}
                params={queryParams}
                request={async (params, sort, filter) => {
                    if (!params.trade_date || !params.strategy_id) {
                        return { data: [], success: true, total: 0 };
                    }

                    try {
                        const sort_config: any[] = [];
                        if (sort && Object.keys(sort).length > 0) {
                            Object.keys(sort).forEach((key) => {
                                sort_config.push({
                                    field: key,
                                    order: sort[key] === 'ascend' ? 'asc' : 'desc',
                                });
                            });
                        }

                        const filter_conditions: any[] = [];
                        if (filter && Object.keys(filter).length > 0) {
                            Object.keys(filter).forEach(key => {
                                if (filter[key]) {
                                    filter_conditions.push({
                                        field: key,
                                        operator: 'IN',
                                        value: filter[key]
                                    });
                                }
                            });
                        }

                        const res = await queryStrategyResults({
                            trade_date: params.trade_date,
                            strategy_id: params.strategy_id,
                            sort_config: sort_config.length > 0 ? sort_config : undefined,
                            filter_conditions: filter_conditions.length > 0 ? filter_conditions : undefined,
                            skip: (params.current! - 1) * params.pageSize!,
                            limit: params.pageSize,
                        });

                        return {
                            data: res.items,
                            success: true,
                            total: res.total,
                        };
                    } catch (error: any) {
                        message.error(error?.response?.data?.detail || '获取结果失败');
                        return { data: [], success: false, total: 0 };
                    }
                }}
                rowKey={(record) => `${record.ts_code}_${record.strategy_id}_${record.trade_date}`}
                pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                }}
                scroll={{ x: 2000 }}
                style={{ marginTop: 16 }}
            />

            <Modal
                title="添加自选"
                open={addFavoriteModalVisible}
                onCancel={() => {
                    setAddFavoriteModalVisible(false);
                    setSelectedStock(null);
                }}
                footer={null}
                width={500}
                centered
                destroyOnClose
            >
                <ProForm
                    formRef={favoriteFormRef}
                    layout="vertical"
                    onFinish={handleAddToFavorite}
                    submitter={{
                        searchConfig: {
                            submitText: '确定',
                            resetText: '取消',
                        },
                        resetButtonProps: {
                            onClick: () => {
                                setAddFavoriteModalVisible(false);
                                setSelectedStock(null);
                            },
                        },
                        render: (props, doms) => (
                            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '16px 0', marginTop: 16, borderTop: '1px solid #f0f0f0' }}>
                                <Space>
                                    {doms}
                                </Space>
                            </div>
                        ),
                    }}
                >
                    <ProFormText
                        name="code"
                        label="股票代码"
                        disabled
                        extra={selectedStock?.name ? `${selectedStock.name}` : ''}
                    />
                    <ProFormTextArea
                        name="comment"
                        label="关注理由"
                        placeholder="请输入关注理由（可选）"
                        fieldProps={{
                            maxLength: 500,
                            showCount: true,
                            rows: 4,
                            autoSize: { minRows: 4, maxRows: 8 },
                        }}
                    />
                </ProForm>
            </Modal>

            {/* 列设置Drawer */}
            <Drawer
                title="列设置"
                open={columnDrawerVisible}
                onClose={() => setColumnDrawerVisible(false)}
                width={400}
            >
                {availableColumns && (
                    <Space direction="vertical" style={{ width: '100%' }}>
                        <div>
                            <Text strong>基础信息</Text>
                            {availableColumns.basic.map((col) => (
                                <div key={col.field} style={{ marginTop: 8 }}>
                                    <Checkbox
                                        checked={selectedColumns.includes(col.field)}
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setSelectedColumns([...selectedColumns, col.field]);
                                            } else {
                                                setSelectedColumns(selectedColumns.filter((c) => c !== col.field));
                                            }
                                        }}
                                    >
                                        {col.label}
                                    </Checkbox>
                                </div>
                            ))}
                        </div>
                        <div>
                            <Text strong>每日指标</Text>
                            {availableColumns.daily_basic.map((col) => (
                                <div key={col.field} style={{ marginTop: 8 }}>
                                    <Checkbox
                                        checked={selectedColumns.includes(col.field)}
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setSelectedColumns([...selectedColumns, col.field]);
                                            } else {
                                                setSelectedColumns(selectedColumns.filter((c) => c !== col.field));
                                            }
                                        }}
                                    >
                                        {col.label}
                                    </Checkbox>
                                </div>
                            ))}
                        </div>
                        <div>
                            <Text strong>日线数据</Text>
                            {availableColumns.daily.map((col) => (
                                <div key={col.field} style={{ marginTop: 8 }}>
                                    <Checkbox
                                        checked={selectedColumns.includes(col.field)}
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setSelectedColumns([...selectedColumns, col.field]);
                                            } else {
                                                setSelectedColumns(selectedColumns.filter((c) => c !== col.field));
                                            }
                                        }}
                                    >
                                        {col.label}
                                    </Checkbox>
                                </div>
                            ))}
                        </div>
                        {availableColumns.factor && (
                            <div>
                                <Text strong>技术指标</Text>
                                {availableColumns.factor.map((col) => (
                                    <div key={col.field} style={{ marginTop: 8 }}>
                                        <Checkbox
                                            checked={selectedColumns.includes(col.field)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setSelectedColumns([...selectedColumns, col.field]);
                                                } else {
                                                    setSelectedColumns(selectedColumns.filter((c) => c !== col.field));
                                                }
                                            }}
                                        >
                                            {col.label}
                                        </Checkbox>
                                    </div>
                                ))}
                            </div>
                        )}
                        {availableColumns.audit && (
                            <div>
                                <Text strong>策略与审计</Text>
                                {availableColumns.audit.map((col) => (
                                    <div key={col.field} style={{ marginTop: 8 }}>
                                        <Checkbox
                                            checked={selectedColumns.includes(col.field)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setSelectedColumns([...selectedColumns, col.field]);
                                                } else {
                                                    setSelectedColumns(selectedColumns.filter((c) => c !== col.field));
                                                }
                                            }}
                                        >
                                            {col.label}
                                        </Checkbox>
                                    </div>
                                ))}
                            </div>
                        )}
                    </Space>
                )}
            </Drawer>
        </Card>
    );
};

export default StrategyStocks;
