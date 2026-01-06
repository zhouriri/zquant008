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
加密货币回测Context对象
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


@dataclass
class CryptoPosition:
    """持仓信息"""

    symbol: str
    quantity: float = 0.0  # 持仓数量(正数多头,负数空头)
    avg_cost: float = 0.0  # 平均成本
    current_price: float = 0.0  # 当前价格
    market_value: float = 0.0  # 市值
    leverage: float = 1.0  # 杠杆倍数
    margin_used: float = 0.0  # 占用保证金

    @property
    def unrealized_pnl(self) -> float:
        """未实现盈亏"""
        return (self.current_price - self.avg_cost) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        """未实现盈亏比例"""
        if self.avg_cost == 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost


@dataclass
class CryptoPortfolio:
    """投资组合"""

    cash: float = 0.0  # 可用资金(USDT)
    positions: dict[str, CryptoPosition] = field(default_factory=dict)  # 持仓字典

    @property
    def total_value(self) -> float:
        """总资产"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    @property
    def total_unrealized_pnl(self) -> float:
        """总未实现盈亏"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_position(self, symbol: str) -> CryptoPosition:
        """获取持仓(如果不存在则创建)"""
        if symbol not in self.positions:
            self.positions[symbol] = CryptoPosition(symbol=symbol)
        return self.positions[symbol]

    def update_position_value(self, symbol: str, price: float):
        """更新持仓市值"""
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.current_price = price
            pos.market_value = pos.quantity * price


@dataclass
class CryptoContext:
    """加密货币回测上下文对象"""

    current_time: datetime  # 当前时间(精确到秒/毫秒)
    portfolio: CryptoPortfolio  # 投资组合
    config: dict  # 回测配置
    exchange_name: str = "binance"  # 交易所名称

    def order(
        self,
        symbol: str,
        quantity: float,
        price: float | None = None,
        order_type: str = "market",
    ):
        """
        下单

        Args:
            symbol: 交易对符号(BTCUSDT)
            quantity: 数量(正数=买入,负数=卖出)
            price: 价格(None表示市价单)
            order_type: 订单类型(market/limit/stop_limit/stop_market)

        Returns:
            订单ID(字符串)
        """
        # 这个方法将在回测引擎中被重写
        # 策略通过context.order()调用,引擎会拦截并处理

    def order_target(self, symbol: str, target_quantity: float, price: float | None = None):
        """
        目标持仓下单

        Args:
            symbol: 交易对符号
            target_quantity: 目标持仓数量
            price: 价格
        """
        current_pos = self.portfolio.get_position(symbol)
        current_quantity = current_pos.quantity
        quantity = target_quantity - current_quantity
        if abs(quantity) > 1e-8:  # 避免浮点数误差
            return self.order(symbol, quantity, price)
        return None

    def order_value(
        self,
        symbol: str,
        value: float,
        price: float | None = None,
        order_type: str = "market",
    ):
        """
        按金额下单

        Args:
            symbol: 交易对符号
            value: 目标金额(正数=买入,负数=卖出)
            price: 价格
            order_type: 订单类型
        """
        if price is None:
            # 使用当前价格
            pos = self.portfolio.get_position(symbol)
            price = pos.current_price if pos.current_price > 0 else 0

        if price > 0:
            quantity = value / price
            return self.order(symbol, quantity, price, order_type)
        return None

    def order_target_value(
        self,
        symbol: str,
        target_value: float,
        price: float | None = None,
    ):
        """
        目标市值下单

        Args:
            symbol: 交易对符号
            target_value: 目标市值
            price: 价格
        """
        if price is None:
            pos = self.portfolio.get_position(symbol)
            price = pos.current_price if pos.current_price > 0 else 0

        if price > 0:
            target_quantity = target_value / price
            return self.order_target(symbol, target_quantity, price)
        return None

    def open_long(
        self,
        symbol: str,
        quantity: float,
        price: float | None = None,
        leverage: float = 1.0,
    ):
        """
        开多仓(合约)

        Args:
            symbol: 交易对符号
            quantity: 数量
            price: 价格
            leverage: 杠杆倍数
        """
        # 设置杠杆
        self.config["leverage"] = leverage
        return self.order(symbol, quantity, price, "market")

    def open_short(
        self,
        symbol: str,
        quantity: float,
        price: float | None = None,
        leverage: float = 1.0,
    ):
        """
        开空仓(合约)

        Args:
            symbol: 交易对符号
            quantity: 数量
            price: 价格
            leverage: 杠杆倍数
        """
        self.config["leverage"] = leverage
        return self.order(symbol, -quantity, price, "market")

    def close_position(
        self,
        symbol: str,
        quantity: float | None = None,
        price: float | None = None,
    ):
        """
        平仓

        Args:
            symbol: 交易对符号
            quantity: 数量(None表示平掉所有仓位)
            price: 价格
        """
        pos = self.portfolio.get_position(symbol)
        if quantity is None:
            quantity = -pos.quantity  # 平掉所有
        return self.order(symbol, quantity, price, "market")
