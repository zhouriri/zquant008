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
加密货币策略示例
"""

from typing import Any, List

import pandas as pd
import numpy as np

from zquant.backtest.strategy import BaseStrategy
from zquant.backtest.crypto_context import CryptoContext


class SimpleMACryptoStrategy(BaseStrategy):
    """
    简单均线策略(加密货币)
    
    策略逻辑:
    - 短期均线(5日)上穿长期均线(20日)时买入
    - 短期均线下穿长期均线时卖出
    """
    
    def initialize(self):
        """策略初始化"""
        self.short_period = 5
        self.long_period = 20
        self.position_size = 0.01  # 0.01 BTC
        self.symbol = "BTCUSDT"
        
        # 历史价格缓存
        self.price_history = []
        
    def on_bar(self, context: CryptoContext, bar_data: dict[str, Any]):
        """K线回调"""
        if self.symbol not in bar_data:
            return
        
        current_bar = bar_data[self.symbol]
        current_price = current_bar["close"]
        
        # 更新价格历史
        self.price_history.append(current_price)
        if len(self.price_history) > self.long_period:
            self.price_history.pop(0)
        
        # 价格数据不足,无法计算均线
        if len(self.price_history) < self.long_period:
            return
        
        # 计算均线
        short_ma = np.mean(self.price_history[-self.short_period:])
        long_ma = np.mean(self.price_history[-self.long_period:])
        
        # 获取当前持仓
        position = context.portfolio.get_position(self.symbol)
        
        # 金叉:短期均线上穿长期均线
        if short_ma > long_ma and position.quantity <= 0:
            context.order(self.symbol, self.position_size)
            print(f"[{context.current_time}] 金叉买入 {self.symbol}: {current_price}")
        
        # 死叉:短期均线下穿长期均线
        elif short_ma < long_ma and position.quantity > 0:
            context.order(self.symbol, -position.quantity)
            print(f"[{context.current_time}] 死叉卖出 {self.symbol}: {current_price}")


class BreakoutCryptoStrategy(BaseStrategy):
    """
    突破策略(加密货币)
    
    策略逻辑:
    - 价格突破最近20根K线最高价时买入
    - 价格跌破最近10根K线最低价时卖出
    """
    
    def initialize(self):
        """策略初始化"""
        self.lookback_period = 20
        self.stoploss_period = 10
        self.position_size = 0.01
        self.symbol = "BTCUSDT"
        
        # K线缓存
        self.bar_history = []
    
    def on_bar(self, context: CryptoContext, bar_data: dict[str, Any]):
        """K线回调"""
        if self.symbol not in bar_data:
            return
        
        current_bar = bar_data[self.symbol]
        
        # 更新K线历史
        self.bar_history.append(current_bar)
        if len(self.bar_history) > self.lookback_period:
            self.bar_history.pop(0)
        
        # K线数据不足
        if len(self.bar_history) < self.lookback_period:
            return
        
        # 获取当前持仓
        position = context.portfolio.get_position(self.symbol)
        
        # 计算突破价
        high_list = [bar["high"] for bar in self.bar_history[:-1]]
        low_list = [bar["low"] for bar in self.bar_history[:-1]]
        
        highest_high = max(high_list)
        lowest_low = min(low_list[-self.stoploss_period:])
        
        current_price = current_bar["close"]
        
        # 突破买入
        if current_price > highest_high and position.quantity <= 0:
            context.order(self.symbol, self.position_size)
            print(f"[{context.current_time}] 突破买入 {self.symbol}: {current_price}")
        
        # 跌破止损
        elif current_price < lowest_low and position.quantity > 0:
            context.order(self.symbol, -position.quantity)
            print(f"[{context.current_time}] 跌破止损 {self.symbol}: {current_price}")


class GridTradingCryptoStrategy(BaseStrategy):
    """
    网格交易策略(加密货币)
    
    策略逻辑:
    - 在一定价格区间内设置多个网格
    - 价格跌到网格价位时买入
    - 价格涨到网格价位时卖出
    """
    
    def initialize(self):
        """策略初始化"""
        self.symbol = "BTCUSDT"
        self.grid_count = 10  # 网格数量
        self.grid_size = 0.002  # 每个网格的比例(0.2%)
        self.position_size = 0.001  # 每格交易量
        
        # 获取初始价格
        self.base_price = None
        self.grid_levels = []
        
        # 记录每个网格的持仓状态
        self.grid_positions = {}  # {grid_price: quantity}
    
    def on_bar(self, context: CryptoContext, bar_data: dict[str, Any]):
        """K线回调"""
        if self.symbol not in bar_data:
            return
        
        current_price = bar_data[self.symbol]["close"]
        
        # 初始化网格
        if self.base_price is None:
            self.base_price = current_price
            self._init_grids(self.base_price)
            print(f"[{context.current_time}] 初始化网格交易: 基准价={self.base_price}")
            return
        
        # 检查每个网格
        for grid_price in self.grid_levels:
            # 价格跌到网格价位,买入
            if abs(current_price - grid_price) / grid_price < 0.001:  # 0.1%容差
                if grid_price not in self.grid_positions or self.grid_positions[grid_price] == 0:
                    context.order(self.symbol, self.position_size)
                    self.grid_positions[grid_price] = self.position_size
                    print(f"[{context.current_time}] 网格买入 {self.symbol} @ {grid_price}")
            
            # 价格涨到网格价位,卖出
            elif abs(current_price - grid_price) / grid_price < 0.001:
                if grid_price in self.grid_positions and self.grid_positions[grid_price] > 0:
                    context.order(self.symbol, -self.grid_positions[grid_price])
                    print(f"[{context.current_time}] 网格卖出 {self.symbol} @ {grid_price}")
                    del self.grid_positions[grid_price]
    
    def _init_grids(self, base_price: float):
        """
        初始化网格价位
        
        Args:
            base_price: 基准价格
        """
        self.grid_levels = []
        
        # 在基准价格上下设置网格
        for i in range(-self.grid_count // 2, self.grid_count // 2 + 1):
            grid_price = base_price * (1 + i * self.grid_size)
            self.grid_levels.append(grid_price)
            self.grid_positions[grid_price] = 0
        
        self.grid_levels.sort()


class RSICryptoStrategy(BaseStrategy):
    """
    RSI策略(加密货币)
    
    策略逻辑:
    - RSI < 30(超卖)时买入
    - RSI > 70(超买)时卖出
    """
    
    def initialize(self):
        """策略初始化"""
        self.rsi_period = 14
        self.overbought_threshold = 70
        self.oversold_threshold = 30
        self.position_size = 0.01
        self.symbol = "BTCUSDT"
        
        # 价格历史
        self.price_history = []
    
    def on_bar(self, context: CryptoContext, bar_data: dict[str, Any]):
        """K线回调"""
        if self.symbol not in bar_data:
            return
        
        current_bar = bar_data[self.symbol]
        current_price = current_bar["close"]
        
        # 更新价格历史
        self.price_history.append(current_price)
        if len(self.price_history) > self.rsi_period + 1:
            self.price_history.pop(0)
        
        # 数据不足
        if len(self.price_history) < self.rsi_period + 1:
            return
        
        # 计算RSI
        rsi = self._calculate_rsi(self.price_history)
        
        # 获取当前持仓
        position = context.portfolio.get_position(self.symbol)
        
        # 超卖买入
        if rsi < self.oversold_threshold and position.quantity <= 0:
            context.order(self.symbol, self.position_size)
            print(f"[{context.current_time}] RSI超卖买入 {self.symbol}: {current_price}, RSI={rsi:.2f}")
        
        # 超买卖出
        elif rsi > self.overbought_threshold and position.quantity > 0:
            context.order(self.symbol, -position.quantity)
            print(f"[{context.current_time}] RSI超买卖出 {self.symbol}: {current_price}, RSI={rsi:.2f}")
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        """
        计算RSI指标
        
        Args:
            prices: 价格列表
            
        Returns:
            RSI值
        """
        if len(prices) < self.rsi_period + 1:
            return 50.0
        
        # 计算涨跌幅
        deltas = np.diff(prices)
        
        # 分离涨跌
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # 计算平均涨跌幅
        avg_gain = np.mean(gains[-self.rsi_period:])
        avg_loss = np.mean(losses[-self.rsi_period:])
        
        # 计算RSI
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class TrendFollowCryptoStrategy(BaseStrategy):
    """
    趋势跟踪策略(加密货币)
    
    策略逻辑:
    - 使用EMA(指数移动平均)判断趋势
    - 价格 > EMA(20) 且 EMA(5) > EMA(20) 时买入
    - 价格 < EMA(20) 或 EMA(5) < EMA(20) 时卖出
    """
    
    def initialize(self):
        """策略初始化"""
        self.short_ema_period = 5
        self.long_ema_period = 20
        self.position_size = 0.01
        self.symbol = "BTCUSDT"
        
        # 价格历史
        self.price_history = []
    
    def on_bar(self, context: CryptoContext, bar_data: dict[str, Any]):
        """K线回调"""
        if self.symbol not in bar_data:
            return
        
        current_bar = bar_data[self.symbol]
        current_price = current_bar["close"]
        
        # 更新价格历史
        self.price_history.append(current_price)
        if len(self.price_history) > self.long_ema_period * 2:
            self.price_history.pop(0)
        
        # 数据不足
        if len(self.price_history) < self.long_ema_period:
            return
        
        # 计算EMA
        short_ema = self._calculate_ema(self.price_history, self.short_ema_period)
        long_ema = self._calculate_ema(self.price_history, self.long_ema_period)
        
        # 获取当前持仓
        position = context.portfolio.get_position(self.symbol)
        
        # 趋势向上
        if current_price > long_ema and short_ema > long_ema and position.quantity <= 0:
            context.order(self.symbol, self.position_size)
            print(f"[{context.current_time}] 趋势向上买入 {self.symbol}: {current_price}")
        
        # 趋势向下
        elif (current_price < long_ema or short_ema < long_ema) and position.quantity > 0:
            context.order(self.symbol, -position.quantity)
            print(f"[{context.current_time}] 趋势向下卖出 {self.symbol}: {current_price}")
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """
        计算EMA(指数移动平均)
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            EMA值
        """
        if len(prices) < period:
            return prices[-1]
        
        # 初始SMA
        sma = np.mean(prices[:period])
        
        # 计算EMA
        multiplier = 2 / (period + 1)
        ema = sma
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
