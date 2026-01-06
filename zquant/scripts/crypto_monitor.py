#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密货币实时监控工具
监控价格变化并发送通知
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from zquant.crypto.exchange_factory import ExchangeFactory


class CryptoMonitor:
    """加密货币监控器"""
    
    def __init__(self, exchange_name: str = "binance"):
        self.exchange = ExchangeFactory.create_exchange(exchange_name)
        self.price_cache = {}
        self.alert_thresholds = {}
    
    def add_alert(self, symbol: str, condition: str, price: float):
        """添加价格告警
        
        Args:
            symbol: 交易对
            condition: 条件 ('above' 或 'below')
            price: 价格
        """
        if symbol not in self.alert_thresholds:
            self.alert_thresholds[symbol] = []
        
        self.alert_thresholds[symbol].append({
            "condition": condition,
            "price": price,
            "triggered": False,
        })
        logger.info(f"添加告警: {symbol} {condition} ${price}")
    
    def check_alerts(self, symbol: str, current_price: float):
        """检查告警条件"""
        if symbol not in self.alert_thresholds:
            return
        
        for alert in self.alert_thresholds[symbol]:
            if alert["triggered"]:
                continue
            
            triggered = False
            if alert["condition"] == "above" and current_price > alert["price"]:
                triggered = True
            elif alert["condition"] == "below" and current_price < alert["price"]:
                triggered = True
            
            if triggered:
                alert["triggered"] = True
                self.send_alert(symbol, current_price, alert)
    
    def send_alert(self, symbol: str, price: float, alert: dict):
        """发送告警通知"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            f"\n{'='*50}\n"
            f"🚨 价格告警触发!\n"
            f"{'='*50}\n"
            f"时间: {now}\n"
            f"交易对: {symbol}\n"
            f"当前价格: ${price:,.2f}\n"
            f"触发条件: {alert['condition']} ${alert['price']:,.2f}\n"
            f"{'='*50}\n"
        )
        print(message)
        logger.warning(message)
    
    async def monitor(self, symbols: list, interval: int = 10):
        """监控交易对价格
        
        Args:
            symbols: 交易对列表
            interval: 刷新间隔(秒)
        """
        logger.info(f"开始监控 {len(symbols)} 个交易对...")
        
        try:
            while True:
                now = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{now}] 更新价格...")
                print("-" * 60)
                
                for symbol in symbols:
                    try:
                        ticker = await self.exchange.get_ticker(symbol)
                        current_price = float(ticker["price"])
                        
                        # 显示价格
                        prev_price = self.price_cache.get(symbol, current_price)
                        change = current_price - prev_price
                        change_pct = (change / prev_price * 100) if prev_price != 0 else 0
                        
                        change_str = ""
                        if change > 0:
                            change_str = f"+{change_pct:.2f}% 📈"
                        elif change < 0:
                            change_str = f"{change_pct:.2f}% 📉"
                        else:
                            change_str = "0.00%"
                        
                        print(f"  {symbol:12} ${current_price:>10,.2f} ({change_str})")
                        
                        # 检查告警
                        self.check_alerts(symbol, current_price)
                        
                        # 更新缓存
                        self.price_cache[symbol] = current_price
                        
                    except Exception as e:
                        logger.error(f"获取 {symbol} 价格失败: {e}")
                
                print("-" * 60)
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("监控已停止")


async def main():
    """主函数"""
    print("=" * 60)
    print("加密货币实时监控工具")
    print("=" * 60)
    
    monitor = CryptoMonitor("binance")
    
    # 添加告警示例
    monitor.add_alert("BTCUSDT", "above", 70000)
    monitor.add_alert("ETHUSDT", "above", 4000)
    monitor.add_alert("BTCUSDT", "below", 60000)
    
    # 监控热门交易对
    symbols = [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "XRPUSDT",
    ]
    
    print(f"\n监控交易对: {', '.join(symbols)}")
    print(f"刷新间隔: 10秒")
    print("按 Ctrl+C 停止监控\n")
    
    await monitor.monitor(symbols, interval=10)


if __name__ == "__main__":
    asyncio.run(main())
