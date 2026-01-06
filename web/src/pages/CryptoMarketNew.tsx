/**
 * 加密货币行情页面 (重构版本)
 *
 * 使用DataTablePage组件，统一数据查询和表格展示逻辑
 */

import { useState } from 'react';
import type { ProColumns } from '@ant-design/pro-components';
import { DataTablePage } from '@/components/DataTablePage';
import { useCryptoPairsQuery, useCryptoRealtime } from '@/hooks/useCryptoDataQuery';
import type { CryptoPair } from '@/types/crypto';

const POPULAR_SYMBOLS = [
  'BTCUSDT',
  'ETHUSDT',
  'BNBUSDT',
  'SOLUSDT',
  'XRPUSDT',
  'ADAUSDT',
  'DOGEUSDT',
  'AVAXUSDT',
];

export default function CryptoMarketNew() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');

  // 使用统一Hook获取实时行情
  const { ticker, formatPrice, formatPercent } = useCryptoRealtime(
    selectedSymbol,
    'binance',
    true,
    3000
  );

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
      title: '计价资产',
      dataIndex: 'quote_asset',
      key: 'quote_asset',
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
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      valueType: 'dateTime',
      search: false,
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          加密货币行情
        </h1>
        <p className="text-gray-600 mt-2">
          实时监控加密货币市场行情
        </p>
      </div>

      {/* 选中交易对详情 */}
      {ticker && (
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-lg mb-6 p-6 text-white">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">{ticker.symbol}</h2>
              <p className="text-blue-100 text-sm mt-1">
                {ticker.exchange?.toUpperCase()}
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">
                ${formatPrice(parseFloat(ticker.price))}
              </div>
              <div className={`text-sm mt-1 ${parseFloat(ticker.price_change_percent || '0') >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                {formatPercent(parseFloat(ticker.price_change_percent || '0'))}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-white/20">
            <div>
              <div className="text-blue-100 text-sm">24h最高</div>
              <div className="font-semibold">
                ${ticker.high_24h?.toLocaleString('en-US') || '-'}
              </div>
            </div>
            <div>
              <div className="text-blue-100 text-sm">24h最低</div>
              <div className="font-semibold">
                ${ticker.low_24h?.toLocaleString('en-US') || '-'}
              </div>
            </div>
            <div>
              <div className="text-blue-100 text-sm">24h交易量</div>
              <div className="font-semibold">
                {(parseFloat(ticker.volume_24h || '0') / 1000000).toFixed(2)}M
              </div>
            </div>
            <div>
              <div className="text-blue-100 text-sm">24h涨跌</div>
              <div className="font-semibold">
                ${ticker.price_change?.toLocaleString('en-US') || '-'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 交易对选择 */}
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <h2 className="text-lg font-semibold mb-4">热门交易对</h2>
        <div className="flex flex-wrap gap-2">
          {POPULAR_SYMBOLS.map((symbol) => (
            <button
              key={symbol}
              onClick={() => setSelectedSymbol(symbol)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedSymbol === symbol
                  ? 'bg-blue-500 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>

      {/* 数据表格 */}
      <DataTablePage<CryptoPair>
        queryFn={async (params) => {
          const { quote_asset, exchange, status, limit } = params;
          const cryptoService = (await import('@/services/cryptoService')).cryptoService;
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
        initialFormValues={{
          quote_asset: 'USDT',
          exchange: undefined,
          status: 'trading',
        }}
      />
    </div>
  );
}
