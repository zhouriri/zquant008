/**
 * 加密货币K线图表页面
 */

import { useState, useEffect } from "react";
import { useCryptoKlines, useCryptoTicker } from "@/hooks";
import type { CryptoTicker } from "@/types/crypto";

export default function CryptoChart() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [selectedInterval, setSelectedInterval] = useState("1h");
  const [chartType, setChartType] = useState<"candlestick" | "line">(
    "candlestick",
  );

  const { klines, loading: klinesLoading, fetchKlines } = useCryptoKlines();
  const { ticker, loading: tickerLoading } = useCryptoTicker(
    selectedSymbol,
    "binance",
    true,
    3000,
  );

  // 获取K线数据
  useEffect(() => {
    if (selectedSymbol) {
      fetchKlines(selectedSymbol, {
        interval: selectedInterval,
        limit: 100,
      });
    }
  }, [selectedSymbol, selectedInterval, fetchKlines]);

  // K线周期选项
  const intervals = [
    { value: "1m", label: "1分钟" },
    { value: "5m", label: "5分钟" },
    { value: "15m", label: "15分钟" },
    { value: "30m", label: "30分钟" },
    { value: "1h", label: "1小时" },
    { value: "4h", label: "4小时" },
    { value: "1d", label: "1天" },
    { value: "1w", label: "1周" },
  ];

  // 热门交易对
  const popularSymbols = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
  ];

  const formatPrice = (price: number) => {
    return price.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">K线图表</h1>
        <p className="text-gray-600 mt-2">查看加密货币价格走势</p>
      </div>

      {/* 工具栏 */}
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex flex-wrap gap-4 items-center">
          {/* 交易对选择 */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              交易对
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {popularSymbols.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </select>
          </div>

          {/* K线周期 */}
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              周期
            </label>
            <select
              value={selectedInterval}
              onChange={(e) => setSelectedInterval(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {intervals.map((interval) => (
                <option key={interval.value} value={interval.value}>
                  {interval.label}
                </option>
              ))}
            </select>
          </div>

          {/* 图表类型 */}
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              图表类型
            </label>
            <select
              value={chartType}
              onChange={(e) =>
                setChartType(e.target.value as "candlestick" | "line")
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="candlestick">K线图</option>
              <option value="line">折线图</option>
            </select>
          </div>

          {/* 当前价格 */}
          {ticker && !tickerLoading && (
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                当前价格
              </label>
              <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-xl font-bold text-blue-700">
                  ${formatPrice(ticker.price)}
                </span>
                {ticker.price_change_percent !== undefined && (
                  <span
                    className={`ml-2 text-sm ${
                      ticker.price_change_percent >= 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {ticker.price_change_percent >= 0 ? "+" : ""}
                    {ticker.price_change_percent.toFixed(2)}%
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* K线图表 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        {klinesLoading ? (
          <div className="flex items-center justify-center h-[500px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <div className="text-gray-500">加载K线数据...</div>
            </div>
          </div>
        ) : klines.length > 0 ? (
          <div>
            {/* ECharts图表占位符 */}
            <div className="flex items-center justify-center h-[500px] border-2 border-dashed border-gray-300 rounded-lg">
              <div className="text-center text-gray-500">
                <svg
                  className="w-16 h-16 mx-auto mb-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 12l3-3 3 3-3M4 14a2 2 0 01-2-2V6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2h-3m-2 4l-3 3 3-3m4-4h-4"
                  />
                </svg>
                <div className="text-lg font-medium mb-2">K线图表</div>
                <div className="text-sm">
                  共 {klines.length} 条数据
                  <br />
                  {selectedSymbol} - {selectedInterval}
                </div>
                <div className="mt-4 text-xs text-gray-400">
                  集成 ECharts 或 TradingView 后即可显示图表
                </div>
              </div>
            </div>

            {/* K线数据表格 */}
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-4">最近K线数据</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        时间
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        开盘
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        最高
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        最低
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        收盘
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        成交量
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {klines.slice(-20).reverse().map((kline, index) => (
                      <tr key={index}>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {new Date(kline.timestamp).toLocaleString("zh-CN", {
                            month: "2-digit",
                            day: "2-digit",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </td>
                        <td
                          className={`px-4 py-3 text-sm ${
                            kline.close >= kline.open
                              ? "text-red-600"
                              : "text-green-600"
                          }`}
                        >
                          {formatPrice(kline.open)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {formatPrice(kline.high)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {formatPrice(kline.low)}
                        </td>
                        <td
                          className={`px-4 py-3 text-sm font-medium ${
                            kline.close >= kline.open
                              ? "text-red-600"
                              : "text-green-600"
                          }`}
                        >
                          {formatPrice(kline.close)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {kline.volume.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-[500px]">
            <div className="text-center text-gray-500">
              <div className="text-lg">暂无K线数据</div>
              <div className="text-sm mt-2">
                请先在同步页面同步K线数据
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
