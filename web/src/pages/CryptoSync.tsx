/**
 * 加密货币数据同步页面
 */

import { useState } from "react";
import { useCryptoPairs } from "@/hooks/useCryptoPairs";
import { cryptoService } from "@/services/cryptoService";
import type { CryptoPair } from "@/types/crypto";

export default function CryptoSync() {
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<{
    type: "pairs" | "klines";
    message: string;
  } | null>(null);

  const { pairs, loading, refetch } = useCryptoPairs({
    quote_asset: "USDT",
    limit: 20,
    autoFetch: true,
  });

  // 交易所配置 (实际应用中应该从用户配置或环境变量获取)
  const exchangeConfig = {
    exchange: "binance",
    api_key: "", // TODO: 从配置获取
    api_secret: "", // TODO: 从配置获取
    passphrase: undefined,
  };

  const handleSyncPairs = async () => {
    setSyncing(true);
    setSyncResult(null);

    try {
      const result = await cryptoService.syncPairs({}, exchangeConfig);
      setSyncResult({
        type: "pairs",
        message: `交易对同步完成! 共${result.synced_count}个`,
      });
      refetch(); // 刷新交易对列表
    } catch (err: any) {
      setSyncResult({
        type: "pairs",
        message: err.response?.data?.message || "同步失败",
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
          interval: "1h",
          days_back: 7,
        },
        exchangeConfig,
      );
      setSyncResult({
        type: "klines",
        message: `K线同步完成! ${symbol} 新增${result.synced_count}条`,
      });
    } catch (err: any) {
      setSyncResult({
        type: "klines",
        message: err.response?.data?.message || "同步失败",
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleBatchSync = async () => {
    setSyncing(true);
    setSyncResult(null);

    try {
      // 批量同步前20个交易对
      const symbols = pairs.slice(0, 20).map((p) => p.symbol);
      for (const symbol of symbols) {
        await handleSyncKlines(symbol);
      }
    } catch (err: any) {
      setSyncResult({
        type: "klines",
        message: "批量同步失败",
      });
    } finally {
      setSyncing(false);
    }
  };

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
            {syncing ? "同步中..." : "同步交易对列表"}
          </button>

          <button
            onClick={handleBatchSync}
            disabled={syncing}
            className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {syncing ? "同步中..." : "批量同步K线(前20个)"}
          </button>
        </div>

        {syncResult && (
          <div
            className={`mt-4 p-4 rounded-lg ${
              syncResult.message.includes("失败")
                ? "bg-red-50 text-red-700"
                : "bg-green-50 text-green-700"
            }`}
          >
            {syncResult.message}
          </div>
        )}
      </div>

      {/* 交易对列表 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">USDT交易对列表</h2>

        {loading ? (
          <div className="text-center text-gray-500 py-8">加载中...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    交易对
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    基础资产
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    交易所
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {pairs.map((pair) => (
                  <tr key={pair.symbol}>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      {pair.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {pair.base_asset}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {pair.exchange}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          pair.status === "trading"
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {pair.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleSyncKlines(pair.symbol)}
                        disabled={syncing}
                        className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                      >
                        同步K线
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
