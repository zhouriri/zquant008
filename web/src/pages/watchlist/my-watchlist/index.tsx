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

import { ProForm, ProFormDatePicker, ProFormText, ProFormTextArea } from '@ant-design/pro-components';
import type { ProColumns, ProFormInstance } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { Button, Card, message, Modal, Popconfirm, Space, Input } from 'antd';
import { useLocation } from '@umijs/max';
import dayjs, { Dayjs } from 'dayjs';
import React, { useEffect, useState, useRef } from 'react';
import { getFavorites, createFavorite, updateFavorite, deleteFavorite } from '@/services/zquant/favorite';
import { getStocks } from '@/services/zquant/data';
import { usePageCache } from '@/hooks/usePageCache';
import { renderDate, renderDateTime } from '@/components/DataTable';

const { TextArea } = Input;

const MyWatchlist: React.FC = () => {
  const location = useLocation();
  const formRef = useRef<ProFormInstance>(null);
  const createFormRef = useRef<ProFormInstance>(null);
  const editFormRef = useRef<ProFormInstance>(null);
  const pageCache = usePageCache();
  const actionRef = useRef<any>(null);
  const isInitialMount = useRef(true);

  const [dataSource, setDataSource] = useState<ZQuant.FavoriteResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingFavorite, setEditingFavorite] = useState<ZQuant.FavoriteResponse | null>(null);
  const [stockOptions, setStockOptions] = useState<{ label: string; value: string }[]>([]);
  const [stockSearchLoading, setStockSearchLoading] = useState(false);

  // 从缓存恢复状态
  useEffect(() => {
    if (!isInitialMount.current) return;
    isInitialMount.current = false;

    const cachedFormValues = pageCache.getFormValues();
    if (cachedFormValues && formRef.current) {
      formRef.current.setFieldsValue(cachedFormValues);
    }
    // ...

    const cachedDataSource = pageCache.getDataSource();
    if (cachedDataSource?.dataSource && cachedDataSource.dataSource.length > 0) {
      setDataSource(cachedDataSource.dataSource);
      setTotal(cachedDataSource.total || 0);
    }

    const cachedCreateModalVisible = pageCache.getModalState('createModal');
    if (cachedCreateModalVisible !== undefined) {
      setCreateModalVisible(cachedCreateModalVisible);
    }

    const cachedEditModalVisible = pageCache.getModalState('editModal');
    if (cachedEditModalVisible !== undefined) {
      setEditModalVisible(cachedEditModalVisible);
    }

    const cachedEditingFavorite = pageCache.get()?.editingFavorite;
    if (cachedEditingFavorite) {
      setEditingFavorite(cachedEditingFavorite);
    }
  }, [pageCache, location.pathname]);

  // 搜索股票（用于股票代码选择器）
  const handleStockSearch = async (searchText: string) => {
    if (!searchText || searchText.length < 2) {
      setStockOptions([]);
      return;
    }

    setStockSearchLoading(true);
    try {
      const response = await getStocks({
        symbol: searchText.length === 6 ? searchText : undefined,
        name: searchText.length !== 6 ? searchText : undefined,
      });
      const options = response.stocks.slice(0, 50).map((stock: any) => ({
        label: `${stock.symbol} - ${stock.name}`,
        value: stock.symbol,
      }));
      setStockOptions(options);
    } catch (error) {
      console.error('搜索股票失败:', error);
    } finally {
      setStockSearchLoading(false);
    }
  };

  // 查询自选列表
  const handleQuery = async (values: any) => {
    try {
      setLoading(true);
      pageCache.saveFormValues(values);

      const params: any = {
        skip: 0,
        limit: 100,
      };

      if (values.code) {
        params.code = values.code;
      }
      if (values.start_date && values.end_date) {
        // 修复 dateRange 格式化问题，确保将值转换为 dayjs 对象后再调用 format 方法
        const startDate = dayjs(values.start_date);
        const endDate = dayjs(values.end_date);
        params.start_date = startDate.format('YYYY-MM-DD');
        params.end_date = endDate.format('YYYY-MM-DD');
      }

      const response = await getFavorites(params);
      setDataSource(response.items);
      setTotal(response.total);

      pageCache.saveDataSource(response.items, undefined, response.total);
      message.success(`查询成功，共${response.total}条记录`);
    } catch (error: any) {
      console.error('Query error:', error);
      console.error('Error response:', error?.response);
      console.error('Error data:', error?.response?.data);
      message.error(error?.response?.data?.detail || error?.message || '查询失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建自选
  const handleCreate = async (values: any) => {
    try {
      await createFavorite({
        code: values.code,
        comment: values.comment,
        fav_datettime: values.fav_datettime ? values.fav_datettime.format('YYYY-MM-DD HH:mm:ss') : undefined,
      });
      message.success('添加自选成功');
      closeCreateModal();
      // 刷新列表

      if (formRef.current) {
        const formValues = formRef.current.getFieldsValue();
        handleQuery(formValues);
      }
      return true;
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '添加自选失败');
      return false;
    }
  };

  // 编辑自选
  const handleEdit = (record: ZQuant.FavoriteResponse) => {
    setEditingFavorite(record);
    setEditModalVisible(true);
    pageCache.saveModalState('editModal', true);
    pageCache.update({ editingFavorite: record });
    setTimeout(() => {
      if (editFormRef.current) {
        editFormRef.current.setFieldsValue({
          comment: record.comment,
          fav_datettime: record.fav_datettime ? dayjs(record.fav_datettime) : undefined,
        });
      }
    }, 100);
  };

  // 更新自选
  const handleUpdate = async (values: any) => {
    if (!editingFavorite) return false;

    try {
      await updateFavorite(editingFavorite.id, {
        comment: values.comment,
        fav_datettime: values.fav_datettime ? dayjs(values.fav_datettime).format('YYYY-MM-DD HH:mm:ss') : undefined,
      });
      message.success('更新自选成功');
      closeEditModal();
      // 刷新列表

      if (formRef.current) {
        const formValues = formRef.current.getFieldsValue();
        handleQuery(formValues);
      }
      return true;
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '更新自选失败');
      return false;
    }
  };

  // 删除自选
  const handleDelete = async (id: number) => {
    try {
      await deleteFavorite(id);
      message.success('删除自选成功');
      // 刷新列表
      if (formRef.current) {
        const formValues = formRef.current.getFieldsValue();
        handleQuery(formValues);
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除自选失败');
    }
  };

  const closeCreateModal = () => {
    setCreateModalVisible(false);
    pageCache.saveModalState('createModal', false);
    if (createFormRef.current) {
      createFormRef.current.resetFields();
    }
  };

  const closeEditModal = () => {
    setEditModalVisible(false);
    setEditingFavorite(null);
    pageCache.saveModalState('editModal', false);
    pageCache.update({ editingFavorite: null });
    if (editFormRef.current) {
      editFormRef.current.resetFields();
    }
  };

  const columns: ProColumns<ZQuant.FavoriteResponse>[] = [

    {
      title: '股票代码',
      dataIndex: 'code',
      width: 100,
      fixed: 'left',
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      width: 150,
      render: (text: string, record: ZQuant.FavoriteResponse) => {
        return text || record.stock_ts_code || '-';
      },
    },
    {
      title: '关注理由',
      dataIndex: 'comment',
      width: 300,
      ellipsis: true,
    },
    {
      title: '自选日期',
      dataIndex: 'fav_datettime',
      width: 180,
      render: (text: string) => renderDateTime(text),
    },
    {
      title: '创建时间',
      dataIndex: 'created_time',
      width: 180,
      render: (text: string) => renderDateTime(text),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_time',
      width: 180,
      render: (text: string) => renderDateTime(text),
    },
    {
      title: '操作',
      width: 150,
      fixed: 'right',
      render: (_: any, record: ZQuant.FavoriteResponse) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这条自选吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <ProForm
        formRef={formRef}
        layout="inline"
        onFinish={handleQuery}
        onValuesChange={() => {
          if (formRef.current) {
            const formValues = formRef.current.getFieldsValue();
            pageCache.saveFormValues(formValues);
          }
        }}
        initialValues={{
          code: '000001',
          start_date: dayjs().subtract(1, 'month'),
          end_date: dayjs(),
        }}
        submitter={{
          render: (props, doms) => {
            return (
              <Space>
                <Button type="primary" key="submit" onClick={() => props.form?.submit?.()}>
                  查询
                </Button>
                <Button
                  key="create"
                  onClick={() => {
                    setCreateModalVisible(true);
                    pageCache.saveModalState('createModal', true);
                  }}
                >
                  添加自选
                </Button>
              </Space>
            );
          },
        }}
      >
        <ProFormText
          name="code"
          label="股票代码"
          placeholder="请输入股票代码，如：000001"
          width="sm"
        />
        <ProFormDatePicker
          name="start_date"
          label="开始日期"
        />
        <ProFormDatePicker
          name="end_date"
          label="结束日期"
        />
      </ProForm>

      <ProTable<ZQuant.FavoriteResponse>
        actionRef={actionRef}
        columns={columns}
        dataSource={dataSource}
        loading={loading}
        search={false}
        scroll={{ x: 1200 }}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          total: total,
        }}
        style={{ marginTop: 16 }}
        rowKey="id"
      />

      {/* 创建自选 Modal */}
      <Modal
        title="添加自选"
        open={createModalVisible}
        onCancel={closeCreateModal}
        footer={null}
        width={600}
        centered
        destroyOnClose
      >

        <ProForm
          formRef={createFormRef}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{
            fav_datettime: dayjs(),
          }}
          submitter={{
            searchConfig: {
              submitText: '确定',
              resetText: '取消',
            },
            resetButtonProps: {
              onClick: () => {
                closeCreateModal();
              },
            },
            render: (props, doms) => {
              return (
                <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '16px 0', marginTop: 16, borderTop: '1px solid #f0f0f0' }}>
                  <Space>
                    {doms}
                  </Space>
                </div>
              );
            },
          }}
        >
          <ProFormText
            name="code"
            label="股票代码"
            placeholder="请输入或搜索股票代码（6位数字）"
            rules={[{ required: true, message: '请输入股票代码' }, { len: 6, message: '股票代码必须为6位数字' }]}
            fieldProps={{
              onSearch: handleStockSearch,
              loading: stockSearchLoading,
            }}
            extra="支持输入股票代码或搜索股票名称"
          />
          <ProFormDatePicker
            name="fav_datettime"
            label="自选日期"
            placeholder="请选择自选日期"
          />
          <ProFormTextArea
            name="comment"
            label="关注理由"
            placeholder="请输入关注理由（可选）"
            fieldProps={{
              maxLength: 2000,
              showCount: true,
              rows: 4,
              autoSize: { minRows: 4, maxRows: 8 },
            }}
          />
        </ProForm>
      </Modal>

      {/* 编辑自选 Modal */}
      <Modal
        title="编辑自选"
        open={editModalVisible}
        onCancel={closeEditModal}
        footer={null}
        width={600}
        centered
        destroyOnClose
      >

        <ProForm
          formRef={editFormRef}
          layout="vertical"
          onFinish={handleUpdate}
          submitter={{
            searchConfig: {
              submitText: '确定',
              resetText: '取消',
            },
            resetButtonProps: {
              onClick: () => {
                closeEditModal();
              },
            },
            render: (props, doms) => {
              return (
                <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '16px 0', marginTop: 16, borderTop: '1px solid #f0f0f0' }}>
                  <Space>
                    {doms}
                  </Space>
                </div>
              );
            },
          }}
        >
          <ProFormText
            name="code"
            label="股票代码"
            disabled
            initialValue={editingFavorite?.code}
          />
          <ProFormDatePicker
            name="fav_datettime"
            label="自选日期"
            placeholder="请选择自选日期"
          />
          <ProFormTextArea
            name="comment"
            label="关注理由"
            placeholder="请输入关注理由（可选）"
            fieldProps={{
              maxLength: 2000,
              showCount: true,
              rows: 4,
              autoSize: { minRows: 4, maxRows: 8 },
            }}
          />
        </ProForm>
      </Modal>
    </Card>
  );
};

export default MyWatchlist;
