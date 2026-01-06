/**
 * 加密货币行情页面
 */

import { useState } from "react";
import { useCryptoTicker } from "@/hooks/useCryptoTicker";
import type { CryptoTicker } from "@/types/crypto";

const POPULAR_SYMBOLS = [
  "BTCUSDT",
  "ETHUSDT",
  "BNBUSDT",
  "SOLUSDT",
  "XRPUSDT",
  "ADAUSDT",
  "DOGEUSDT",
  "AVAXUSDT",
];

export default function CryptoMarket() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [tickers, setTickers] = useState<Record<string, CryptoTicker>>({});

  // 获取选中交易对的详细信息
  const { ticker, loading, error } = useCryptoTicker(
    selectedSymbol,
    "binance",
    true, // 自动刷新
    3000, // 3秒刷新
  );

  // 获取所有热门交易对的行情
  // 注意: 实际应用中应该使用WebSocket实现
  const fetchAllTickers = async () => {
    // TODO: 实现批量获取
  };

  const formatPrice = (price: number) => {
    return price.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const formatPercent = (percent: number) => {
    const color = percent >= 0 ? "text-green-500" : "text-red-500";
    const sign = percent >= 0 ? "+" : "";
    return <span className={color}>{sign}{percent.toFixed(2)}%</span>;
  };

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

      {/* 交易对选择 */}
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <h2 className="text-lg font-semibold mb-4">热门交易对</h2>
        <div className="flex flex-wrap gap-2">
          {POPULAR_SYMBOLS.map((symbol) => (
            <button
              key={symbol}
              onClick={() => setSelectedSymbol(symbol)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedSymbol === symbol
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>

      {/* 选中交易对详情 */}
      {loading ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center text-gray-500">加载中...</div>
        </div>
      ) : error ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center text-red-500">{error}</div>
        </div>
      ) : ticker ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">{ticker.symbol}</h2>
              <p className="text-gray-500">{ticker.exchange}</p>
            </div>
            <div>
              <div className="text-3xl font-bold">
                ${formatPrice(ticker.price)}
              </div>
              <div className="text-lg">
                {ticker.price_change_percent !== undefined && (
                  formatPercent(ticker.price_change_percent)
                )}
              </div>
            </div>
          </div>

          {/* 24小时统计数据 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">24h最高</div>
              <div className="text-xl font-semibold">
                {ticker.high_24h ? formatPrice(ticker.high_24h) : "-"}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">24h最低</div>
              <div className="text-xl font-semibold">
                {ticker.low_24h ? formatPrice(ticker.low_24h) : "-"}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">24h涨跌</div>
              <div className="text-xl font-semibold">
                {ticker.price_change !== undefined
                  ? formatPrice(ticker.price_change)
                  : "-"}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">24h成交量</div>
              <div className="text-xl font-semibold">
                {ticker.volume_24h
                  ? ticker.volume_24h.toLocaleString()
                  : "-"}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* 交易对列表 */}
      <div className="bg-white rounded-lg shadow mt-6 p-4">
        <h2 className="text-lg font-semibold mb-4">所有交易对</h2>
        <div className="text-gray-500 text-center py-8">
          功能开发中...
          <br />
          <span className="text-sm">
            敬请期待完整交易对列表和K线图表功能
          </span>
        </div>
      </div>
    </div>
  );
}
