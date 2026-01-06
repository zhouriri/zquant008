/**
 * 加密货币数据同步页面 (重构版本)
 *
 * 使用DataTablePage组件，统一数据查询和表格展示逻辑
 */

import { useState } from 'react';
import type { ProColumns } from '@ant-design/pro-components';
import { DataTablePage } from '@/components/DataTablePage';
import { cryptoService } from '@/services/cryptoService';
import type { CryptoPair } from '@/types/crypto';

export default function CryptoSyncNew() {
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<{
    type: 'pairs' | 'klines' | 'batch';
    message: string;
  } | null>(null);

  // 交易所配置 (实际应用中应该从用户配置或环境变量获取)
  const exchangeConfig = {
    exchange: 'binance',
    api_key: '', // TODO: 从配置获取
    api_secret: '', // TODO: 从配置获取
    passphrase: undefined,
  };

  const handleSyncPairs = async () => {
    setSyncing(true);
    setSyncResult(null);

    try {
      const result = await cryptoService.syncPairs({}, exchangeConfig);
      setSyncResult({
        type: 'pairs',
        message: `交易对同步完成! 共${result.synced_count}个`,
      });
    } catch (err: any) {
      setSyncResult({
        type: 'pairs',
        message: err.response?.data?.message || '同步失败',
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleBatchSync = async (symbols: string[]) => {
    setSyncing(true);
    setSyncResult(null);

    try {
      // 批量同步K线
      for (const symbol of symbols) {
        const result = await cryptoService.syncKlines(
          {
            symbol,
            interval: '1h',
            days_back: 7,
          },
          exchangeConfig,
        );
        console.log(`${symbol} 同步完成: ${result.synced_count}条`);
      }
      setSyncResult({
        type: 'batch',
        message: `批量同步完成! 共${symbols.length}个交易对`,
      });
    } catch (err: any) {
      setSyncResult({
        type: 'batch',
        message: '批量同步失败',
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncKlines = async (symbol: string) => {
    setSyncing(true);
    setSyncResult(null);

    try {
      const result = await cryptoService.syncKlines(
        {
          symbol,
          interval: '1h',
          days_back: 7,
        },
        exchangeConfig,
      );
      setSyncResult({
        type: 'klines',
        message: `K线同步完成! ${symbol} 新增${result.synced_count}条`,
      });
    } catch (err: any) {
      setSyncResult({
        type: 'klines',
        message: err.response?.data?.message || '同步失败',
      });
    } finally {
      setSyncing(false);
    }
  };

  // 定义表格列
  const columns: ProColumns<CryptoPair>[] = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
      fixed: 'left',
      render: (_, record) => (
        <span className="font-semibold">{record.symbol}</span>
      ),
    },
    {
      title: '基础资产',
      dataIndex: 'base_asset',
      key: 'base_asset',
      width: 100,
    },
    {
      title: '交易所',
      dataIndex: 'exchange',
      key: 'exchange',
      width: 100,
      valueEnum: {
        binance: { text: 'Binance', status: 'Success' },
        okx: { text: 'OKX', status: 'Processing' },
        bybit: { text: 'Bybit', status: 'Default' },
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      valueEnum: {
        trading: { text: '交易中', status: 'Success' },
        break: { text: '暂停', status: 'Warning' },
        closed: { text: '已下架', status: 'Error' },
      },
    },
    {
      title: '24h交易量',
      dataIndex: 'volume_24h',
      key: 'volume_24h',
      width: 150,
      render: (volume: number) => volume?.toLocaleString('en-US') || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <a
          onClick={() => handleSyncKlines(record.symbol)}
          disabled={syncing}
          className={syncing ? 'text-gray-400 cursor-not-allowed' : ''}
        >
          同步K线
        </a>
      ),
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          加密货币数据同步
        </h1>
        <p className="text-gray-600 mt-2">
          手动同步加密货币交易对和K线数据
        </p>
      </div>

      {/* 提示信息 */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-yellow-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              请先在配置页面设置交易所API密钥,才能进行数据同步。
            </p>
          </div>
        </div>
      </div>

      {/* 同步操作区 */}
      <div className="bg-white rounded-lg shadow mb-6 p-6">
        <h2 className="text-lg font-semibold mb-4">数据同步操作</h2>

        <div className="flex gap-4 flex-wrap">
          <button
            onClick={handleSyncPairs}
            disabled={syncing}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {syncing ? '同步中...' : '同步交易对列表'}
          </button>
        </div>

        {syncResult && (
          <div
            className={`mt-4 p-4 rounded-lg ${
              syncResult.message.includes('失败')
                ? 'bg-red-50 text-red-700'
                : 'bg-green-50 text-green-700'
            }`}
          >
            {syncResult.message}
          </div>
        )}
      </div>

      {/* 数据表格 */}
      <DataTablePage<CryptoPair>
        queryFn={async (params) => {
          const { quote_asset, exchange, status, limit } = params;
          return await cryptoService.getPairs({
            quote_asset,
            exchange,
            status: status || 'trading',
            limit: limit || 100,
          });
        }}
        getItems={(response) => response.data || []}
        getKey={(item, index) => item.symbol || index}
        columns={columns}
        tableTitle="交易对列表"
        queryOptions={{
          enableCache: true,
        }}
        showFetchButton={true}
        onFetch={async (values) => {
          const { dataSource } = values;
          if (dataSource && dataSource.length > 0) {
            const symbols = dataSource.slice(0, 10).map((p: CryptoPair) => p.symbol);
            await handleBatchSync(symbols);
          }
        }}
        initialFormValues={{
          quote_asset: 'USDT',
          exchange: undefined,
          status: 'trading',
        }}
      />
    </div>
  );
}
