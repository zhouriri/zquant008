/**
 * 加密货币策略回测页面
 */

import { useState } from "react";
import type { CryptoBacktestConfig } from "@/types/crypto";

export default function CryptoBacktest() {
  const [config, setConfig] = useState<CryptoBacktestConfig>({
    initial_capital: 10000.0,
    exchange: "binance",
    symbols: ["BTCUSDT"],
    interval: "1h",
    start_time: "",
    end_time: "",
    maker_fee: 0.001,
    taker_fee: 0.001,
    slippage_rate: 0.0005,
  });

  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any | null>(null);

  // 策略选项
  const strategies = [
    { value: "SimpleMACryptoStrategy", label: "简单均线策略" },
    { value: "BreakoutCryptoStrategy", label: "突破策略" },
    { value: "GridTradingCryptoStrategy", label: "网格交易策略" },
    { value: "RSICryptoStrategy", label: "RSI策略" },
    { value: "TrendFollowCryptoStrategy", label: "趋势跟踪策略" },
  ];

  const [selectedStrategy, setSelectedStrategy] = useState(
    "SimpleMACryptoStrategy",
  );

  // K线周期选项
  const intervals = [
    { value: "5m", label: "5分钟" },
    { value: "15m", label: "15分钟" },
    { value: "30m", label: "30分钟" },
    { value: "1h", label: "1小时" },
    { value: "4h", label: "4小时" },
    { value: "1d", label: "1天" },
  ];

  const handleRunBacktest = async () => {
    setRunning(true);
    setResults(null);

    try {
      // TODO: 调用回测API
      // const response = await backtestService.runCryptoBacktest({
      //   ...config,
      //   strategy: selectedStrategy,
      // });
      // setResults(response.data);

      // 模拟结果
      setTimeout(() => {
        setResults({
          initial_capital: config.initial_capital,
          final_value: config.initial_capital * 1.15,
          total_return: 0.15,
          total_return_pct: 15.0,
          total_trades: 42,
          win_rate: 0.65,
          max_drawdown: -0.08,
          sharpe_ratio: 2.3,
        });
        setRunning(false);
      }, 2000);
    } catch (error) {
      console.error("回测失败:", error);
      setRunning(false);
    }
  };

  const formatPercent = (value: number) => {
    const color = value >= 0 ? "text-green-600" : "text-red-600";
    return (
      <span className={color}>
        {value >= 0 ? "+" : ""}
        {(value * 100).toFixed(2)}%
      </span>
    );
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          策略回测
        </h1>
        <p className="text-gray-600 mt-2">
          使用历史数据测试加密货币策略
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 回测配置 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">回测配置</h2>

          <div className="space-y-4">
            {/* 策略选择 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                选择策略
              </label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {strategies.map((strategy) => (
                  <option key={strategy.value} value={strategy.value}>
                    {strategy.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 初始资金 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                初始资金 (USDT)
              </label>
              <input
                type="number"
                value={config.initial_capital}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    initial_capital: parseFloat(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                step="100"
              />
            </div>

            {/* 交易所 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                交易所
              </label>
              <select
                value={config.exchange}
                onChange={(e) =>
                  setConfig({ ...config, exchange: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="binance">Binance</option>
                <option value="okx">OKX</option>
                <option value="bybit">Bybit</option>
              </select>
            </div>

            {/* 交易对 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                交易对
              </label>
              <input
                type="text"
                value={config.symbols.join(",")}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    symbols: e.target.value.split(",").map((s) => s.trim()),
                  })
                }
                placeholder="BTCUSDT,ETHUSDT"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* K线周期 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                K线周期
              </label>
              <select
                value={config.interval}
                onChange={(e) =>
                  setConfig({ ...config, interval: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {intervals.map((interval) => (
                  <option key={interval.value} value={interval.value}>
                    {interval.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 日期范围 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  开始日期
                </label>
                <input
                  type="date"
                  value={config.start_time}
                  onChange={(e) =>
                    setConfig({ ...config, start_time: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  结束日期
                </label>
                <input
                  type="date"
                  value={config.end_time}
                  onChange={(e) =>
                    setConfig({ ...config, end_time: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* 手续费设置 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Maker费率
                </label>
                <input
                  type="number"
                  value={config.maker_fee}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      maker_fee: parseFloat(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  step="0.0001"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Taker费率
                </label>
                <input
                  type="number"
                  value={config.taker_fee}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      taker_fee: parseFloat(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  step="0.0001"
                  min="0"
                />
              </div>
            </div>

            {/* 滑点率 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                滑点率
              </label>
              <input
                type="number"
                value={config.slippage_rate}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    slippage_rate: parseFloat(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                step="0.0001"
                min="0"
              />
            </div>

            {/* 运行按钮 */}
            <button
              onClick={handleRunBacktest}
              disabled={running}
              className="w-full px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {running ? "回测中..." : "开始回测"}
            </button>
          </div>
        </div>

        {/* 回测结果 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">回测结果</h2>

          {results ? (
            <div className="space-y-4">
              {/* 核心指标 */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">总收益率</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {formatPercent(results.total_return)}
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">胜率</div>
                  <div className="text-2xl font-bold text-green-700">
                    {(results.win_rate * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* 资金统计 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">初始资金</div>
                    <div className="text-xl font-semibold">
                      ${results.initial_capital.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">最终资金</div>
                    <div className="text-xl font-semibold">
                      ${results.final_value.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              {/* 交易统计 */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">总交易次数</div>
                  <div className="text-xl font-semibold">
                    {results.total_trades}次
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">最大回撤</div>
                  <div className="text-xl font-semibold">
                    {formatPercent(results.max_drawdown)}
                  </div>
                </div>
              </div>

              {/* 风险指标 */}
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">夏普比率</div>
                <div className="text-2xl font-bold text-purple-700">
                  {results.sharpe_ratio.toFixed(2)}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <div className="text-lg">配置回测参数并运行回测</div>
              <div className="text-sm mt-2">结果将显示在这里</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
