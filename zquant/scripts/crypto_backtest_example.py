# Copyright 2025 ZQuant Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
加密货币回测示例
"""

from datetime import datetime, timedelta, timezone

from zquant.backtest.crypto_engine import CryptoBacktestEngine
from zquant.strategies.crypto_strategies import (
    SimpleMACryptoStrategy,
    BreakoutCryptoStrategy,
    GridTradingCryptoStrategy,
    RSICryptoStrategy,
    TrendFollowCryptoStrategy,
)


def run_ma_strategy():
    """运行均线策略回测"""
    print("=" * 60)
    print("简单均线策略回测")
    print("=" * 60)
    
    config = {
        "initial_capital": 10000.0,  # 初始资金10000 USDT
        "exchange": "binance",
        "symbols": ["BTCUSDT"],
        "interval": "1h",
        "start_time": datetime.now(timezone.utc) - timedelta(days=30),
        "end_time": datetime.now(timezone.utc),
        "maker_fee": 0.001,  # Maker费率0.1%
        "taker_fee": 0.001,  # Taker费率0.1%
        "slippage_rate": 0.0005,  # 滑点率0.05%
    }
    
    engine = CryptoBacktestEngine(SimpleMACryptoStrategy, config)
    results = engine.run()
    
    print(f"\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:.2f}")
    print(f"最终价值: ${results['final_value']:.2f}")
    print(f"总收益率: {results['total_return_pct']:.2f}%")
    print(f"总交易次数: {results['total_trades']}")
    print()


def run_breakout_strategy():
    """运行突破策略回测"""
    print("=" * 60)
    print("突破策略回测")
    print("=" * 60)
    
    config = {
        "initial_capital": 10000.0,
        "exchange": "binance",
        "symbols": ["BTCUSDT"],
        "interval": "1h",
        "start_time": datetime.now(timezone.utc) - timedelta(days=30),
        "end_time": datetime.now(timezone.utc),
        "maker_fee": 0.001,
        "taker_fee": 0.001,
        "slippage_rate": 0.0005,
    }
    
    engine = CryptoBacktestEngine(BreakoutCryptoStrategy, config)
    results = engine.run()
    
    print(f"\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:.2f}")
    print(f"最终价值: ${results['final_value']:.2f}")
    print(f"总收益率: {results['total_return_pct']:.2f}%")
    print(f"总交易次数: {results['total_trades']}")
    print()


def run_rsi_strategy():
    """运行RSI策略回测"""
    print("=" * 60)
    print("RSI策略回测")
    print("=" * 60)
    
    config = {
        "initial_capital": 10000.0,
        "exchange": "binance",
        "symbols": ["BTCUSDT"],
        "interval": "1h",
        "start_time": datetime.now(timezone.utc) - timedelta(days=30),
        "end_time": datetime.now(timezone.utc),
        "maker_fee": 0.001,
        "taker_fee": 0.001,
        "slippage_rate": 0.0005,
    }
    
    engine = CryptoBacktestEngine(RSICryptoStrategy, config)
    results = engine.run()
    
    print(f"\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:.2f}")
    print(f"最终价值: ${results['final_value']:.2f}")
    print(f"总收益率: {results['total_return_pct']:.2f}%")
    print(f"总交易次数: {results['total_trades']}")
    print()


def run_trend_follow_strategy():
    """运行趋势跟踪策略回测"""
    print("=" * 60)
    print("趋势跟踪策略回测")
    print("=" * 60)
    
    config = {
        "initial_capital": 10000.0,
        "exchange": "binance",
        "symbols": ["BTCUSDT"],
        "interval": "1h",
        "start_time": datetime.now(timezone.utc) - timedelta(days=30),
        "end_time": datetime.now(timezone.utc),
        "maker_fee": 0.001,
        "taker_fee": 0.001,
        "slippage_rate": 0.0005,
    }
    
    engine = CryptoBacktestEngine(TrendFollowCryptoStrategy, config)
    results = engine.run()
    
    print(f"\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:.2f}")
    print(f"最终价值: ${results['final_value']:.2f}")
    print(f"总收益率: {results['total_return_pct']:.2f}%")
    print(f"总交易次数: {results['total_trades']}")
    print()


if __name__ == "__main__":
    # 运行所有策略回测
    run_ma_strategy()
    run_breakout_strategy()
    run_rsi_strategy()
    run_trend_follow_strategy()
    
    print("=" * 60)
    print("所有策略回测完成!")
    print("=" * 60)
