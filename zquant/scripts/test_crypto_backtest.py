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
测试加密货币回测引擎
"""

from datetime import datetime, timedelta, timezone

from zquant.backtest.crypto_engine import CryptoBacktestEngine
from zquant.strategies.crypto_strategies import SimpleMACryptoStrategy


def test_crypto_backtest():
    """测试加密货币回测引擎"""
    
    print("=" * 60)
    print("测试加密货币回测引擎")
    print("=" * 60)
    
    # 配置回测
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
    
    # 创建回测引擎
    engine = CryptoBacktestEngine(SimpleMACryptoStrategy, config)
    
    # 运行回测
    print("\n开始回测...")
    results = engine.run()
    
    # 显示结果
    print("\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:.2f}")
    print(f"最终价值: ${results['final_value']:.2f}")
    print(f"总收益率: {results['total_return_pct']:.2f}%")
    print(f"总交易次数: {results['total_trades']}")
    print(f"回测时间: {results['start_time']} -> {results['end_time']}")
    
    # 显示持仓信息
    print("\n持仓信息:")
    portfolio = engine.context.portfolio
    print(f"可用资金: ${portfolio.cash:.2f}")
    print(f"持仓市值: ${portfolio.market_value:.2f}")
    print(f"总资产: ${portfolio.total_value:.2f}")
    
    for symbol, position in portfolio.positions.items():
        if position.quantity > 0:
            print(f"  {symbol}: {position.quantity:.4f} @ {position.current_price:.2f}")
    
    print("\n测试完成!")


if __name__ == "__main__":
    test_crypto_backtest()
