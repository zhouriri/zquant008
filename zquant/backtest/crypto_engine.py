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
加密货币回测引擎
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
import uuid

import pandas as pd
from loguru import logger
from sqlalchemy.orm import Session

from zquant.backtest.context import Context, Order, OrderSide, OrderStatus
from zquant.backtest.cost import CostCalculator, CostConfig
from zquant.backtest.crypto_context import CryptoContext, CryptoPortfolio
from zquant.backtest.crypto_cost import CryptoCostCalculator, CryptoCostConfig


class CryptoBacktestEngine:
    """加密货币回测引擎"""

    def __init__(self, strategy_class: type, config: dict[str, Any]):
        """
        初始化回测引擎

        Args:
            strategy_class: 策略类(不是实例)
            config: 回测配置
        """
        self.strategy_class = strategy_class
        self.config = config

        # 初始化Context
        initial_cash = config.get("initial_capital", 1000000.0)
        exchange_name = config.get("exchange", "binance")
        self.context = CryptoContext(
            current_time=None,
            portfolio=CryptoPortfolio(cash=initial_cash),
            config=config,
            exchange_name=exchange_name,
        )

        # 重写context.order方法,使其由引擎处理
        self.context.order = self._create_order

        # 成本计算器
        cost_config = CryptoCostConfig(
            exchange=exchange_name,
            maker_fee=config.get("maker_fee", 0.001),
            taker_fee=config.get("taker_fee", 0.001),
            slippage_rate=config.get("slippage_rate", 0.0005),
        )
        self.cost_calculator = CryptoCostCalculator(cost_config)

        # 订单管理(T+0即时成交)
        self.pending_orders: dict[str, Order] = {}  # 待成交订单
        self.filled_orders: List[Order] = []  # 已成交订单

        # 数据
        self.start_time = config["start_time"]
        self.end_time = config["end_time"]
        self.symbols = config.get("symbols", ["BTCUSDT"])
        self.interval = config.get("interval", "1h")

    def _create_order(
        self,
        symbol: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> str:
        """
        创建订单(由context.order调用)

        Args:
            symbol: 交易对符号
            quantity: 数量
            price: 价格(None表示市价单)
            order_type: 订单类型

        Returns:
            订单ID
        """
        order_id = str(uuid.uuid4())
        
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY if quantity > 0 else OrderSide.SELL,
            quantity=abs(quantity),
            filled_quantity=0.0,
            price=price,
            filled_price=0.0,
            order_time=self.context.current_time,
            fill_time=None,
            status=OrderStatus.PENDING,
            commission=0.0,
            tax=0.0,
            slippage=0.0,
        )
        
        self.pending_orders[order_id] = order
        
        # 币圈T+0,立即撮合
        self._match_order(order)
        
        return order_id

    def _match_order(self, order: Order):
        """
        撮合订单(T+0即时成交)

        Args:
            order: 待撮合订单
        """
        # 获取当前价格
        # TODO: 从K线数据中获取当前价格
        current_price = 67500.0  # 临时值

        # 市价单使用当前价格
        fill_price = order.price if order.price else current_price

        # 计算成本(Maker/Taker)
        is_maker = order.price is not None  # 限价单为Maker,市价单为Taker
        cost_result = self.cost_calculator.apply_costs_to_order(
            {"quantity": order.quantity if order.side == OrderSide.BUY else -order.quantity},
            fill_price=fill_price,
            is_maker=is_maker,
        )

        # 更新订单状态
        order.filled_quantity = order.quantity
        order.filled_price = fill_price
        order.fill_time = self.context.current_time
        order.status = OrderStatus.FILLED
        order.commission = cost_result["fee"]
        order.slippage = cost_result["slippage"]

        # 移入已成交订单
        self.filled_orders.append(order)
        del self.pending_orders[order.order_id]

        # 更新投资组合
        self._update_portfolio(order, fill_price, cost_result)

    def _update_portfolio(self, order: Order, fill_price: float, cost_result: dict):
        """
        更新投资组合

        Args:
            order: 成交订单
            fill_price: 成交价格
            cost_result: 成本结果
        """
        symbol = order.symbol
        pos = self.context.portfolio.get_position(symbol)

        if order.side == OrderSide.BUY:
            # 买入:减少现金,增加持仓
            cost = order.quantity * fill_price + cost_result["total"]
            self.context.portfolio.cash -= cost
            
            # 更新持仓成本(加权平均)
            total_cost = pos.avg_cost * pos.quantity + order.quantity * fill_price
            total_quantity = pos.quantity + order.quantity
            pos.avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
            pos.quantity = total_quantity
        else:
            # 卖出:增加现金,减少持仓
            revenue = order.quantity * fill_price - cost_result["total"]
            self.context.portfolio.cash += revenue
            
            pos.quantity -= order.quantity

        # 更新持仓市值
        pos.current_price = fill_price
        pos.market_value = pos.quantity * fill_price

    def run(self) -> dict[str, Any]:
        """
        运行回测

        Returns:
            回测结果字典
        """
        logger.info(f"开始加密货币回测: {self.start_time} -> {self.end_time}")
        
        # TODO: 加载K线数据
        # klines_data = self._load_klines_data()
        
        # 模拟回测循环
        # for timestamp, bar_data in klines_data.items():
        #     self.context.current_time = timestamp
        #     
        #     # 更新持仓市值
        #     for symbol in self.symbols:
        #         if symbol in bar_data:
        #             self.context.portfolio.update_position_value(symbol, bar_data[symbol]['close'])
        #     
        #     # 调用策略
        #     self.strategy.on_bar(self.context, bar_data)

        # 临时: 模拟100根K线
        for i in range(100):
            self.context.current_time = self.start_time + timedelta(hours=i)
            
            # 模拟价格数据
            bar_data = {}
            for symbol in self.symbols:
                bar_data[symbol] = {
                    "open": 67000.0 + i * 10,
                    "high": 67200.0 + i * 10,
                    "low": 66800.0 + i * 10,
                    "close": 67100.0 + i * 10,
                    "volume": 100.0 + i,
                }
                
                # 更新持仓市值
                self.context.portfolio.update_position_value(symbol, bar_data[symbol]["close"])
            
            # 调用策略
            try:
                self.strategy.on_bar(self.context, bar_data)
            except Exception as e:
                logger.error(f"策略执行错误: {e}")

        logger.info("回测完成")

        # 计算绩效
        return self._calculate_performance()

    def _load_klines_data(self) -> dict[datetime, dict[str, Any]]:
        """
        加载K线数据

        Returns:
            按时间戳索引的K线数据
        """
        # TODO: 从数据库或交易所API加载K线数据
        return {}

    def _calculate_performance(self) -> dict[str, Any]:
        """
        计算回测绩效指标

        Returns:
            绩效指标字典
        """
        final_value = self.context.portfolio.total_value
        initial_value = self.config["initial_capital"]

        total_return = (final_value - initial_value) / initial_value
        
        # TODO: 计算更详细的绩效指标
        # - 最大回撤
        # - 夏普比率
        # - 胜率
        # - 盈亏比

        return {
            "initial_capital": initial_value,
            "final_value": final_value,
            "total_return": total_return,
            "total_return_pct": total_return * 100,
            "total_trades": len(self.filled_orders),
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
