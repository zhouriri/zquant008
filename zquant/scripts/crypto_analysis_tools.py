#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密货币数据分析工具集
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from zquant.common.database import get_db
from zquant.models import CryptoPair, CryptoKline, get_kline_table_name
from zquant.models.crypto import create_kline_table_class


class CryptoAnalyzer:
    """加密货币数据分析工具"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_top_pairs_by_volume(self, limit: int = 10) -> List[Dict]:
        """获取交易量最大的交易对"""
        pairs = self.session.query(CryptoPair).order_by(
            CryptoPair.volume_24h.desc()
        ).limit(limit).all()
        
        return [
            {
                "symbol": p.symbol,
                "base_asset": p.base_asset,
                "quote_asset": p.quote_asset,
                "volume_24h": p.volume_24h,
                "price_change_24h": p.price_change_24h,
                "price_change_percent_24h": p.price_change_percent_24h,
            }
            for p in pairs
        ]
    
    def analyze_kline_data(
        self,
        symbol: str,
        interval: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """分析K线数据"""
        table_name = get_kline_table_name(interval)
        KlineTable = create_kline_table_class(table_name)
        
        start_time = datetime.now() - timedelta(days=days)
        
        klines = self.session.query(KlineTable).filter(
            KlineTable.symbol == symbol,
            KlineTable.open_time >= start_time
        ).order_by(KlineTable.open_time).all()
        
        if not klines:
            return {"error": "No data found"}
        
        # 转换为DataFrame
        df = pd.DataFrame([
            {
                "timestamp": k.open_time,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
            }
            for k in klines
        ])
        
        # 计算指标
        df["returns"] = df["close"].pct_change()
        df["ma7"] = df["close"].rolling(window=7).mean()
        df["ma30"] = df["close"].rolling(window=30).mean()
        
        return {
            "symbol": symbol,
            "interval": interval,
            "period": f"{days} days",
            "data_points": len(df),
            "current_price": df["close"].iloc[-1],
            "price_change": df["close"].iloc[-1] - df["close"].iloc[0],
            "price_change_percent": (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100,
            "max_price": df["high"].max(),
            "min_price": df["low"].min(),
            "avg_volume": df["volume"].mean(),
            "volatility": df["returns"].std() * 100,
            "trend": "up" if df["ma7"].iloc[-1] > df["ma30"].iloc[-1] else "down",
        }
    
    def get_price_correlation(
        self,
        symbols: List[str],
        interval: str,
        days: int = 30
    ) -> pd.DataFrame:
        """计算价格相关性"""
        price_data = {}
        
        for symbol in symbols:
            table_name = get_kline_table_name(interval)
            KlineTable = create_kline_table_class(table_name)
            
            start_time = datetime.now() - timedelta(days=days)
            klines = self.session.query(KlineTable).filter(
                KlineTable.symbol == symbol,
                KlineTable.open_time >= start_time
            ).order_by(KlineTable.open_time).all()
            
            if klines:
                df = pd.DataFrame([k.close for k in klines], columns=[symbol])
                price_data[symbol] = df[symbol].pct_change().dropna()
        
        if len(price_data) < 2:
            return pd.DataFrame()
        
        # 计算相关性矩阵
        correlation_df = pd.DataFrame(price_data).corr()
        return correlation_df


async def main():
    """主函数"""
    print("=" * 60)
    print("加密货币数据分析工具")
    print("=" * 60)
    
    db_gen = get_db()
    db = next(db_gen)
    
    analyzer = CryptoAnalyzer(db)
    
    # 1. 热门交易对
    print("\n[1] 热门交易对 (按交易量)")
    print("-" * 60)
    top_pairs = analyzer.get_top_pairs_by_volume(10)
    for pair in top_pairs:
        print(f"  {pair['symbol']:12} | "
              f"24h量: {pair['volume_24h']:>15,.2f} | "
              f"24h涨跌: {pair['price_change_percent_24h']:>7.2f}%")
    
    # 2. BTC分析
    print("\n[2] BTC/USDT 30天分析")
    print("-" * 60)
    btc_analysis = analyzer.analyze_kline_data("BTCUSDT", "1d", 30)
    if "error" not in btc_analysis:
        print(f"  当前价格: ${btc_analysis['current_price']:,.2f}")
        print(f"  30天涨跌: {btc_analysis['price_change_percent']:.2f}%")
        print(f"  最高价格: ${btc_analysis['max_price']:,.2f}")
        print(f"  最低价格: ${btc_analysis['min_price']:,.2f}")
        print(f"  波动率: {btc_analysis['volatility']:.2f}%")
        print(f"  趋势: {btc_analysis['trend']}")
    
    # 3. 价格相关性
    print("\n[3] 主要币种价格相关性")
    print("-" * 60)
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
    correlation = analyzer.get_price_correlation(symbols, "1d", 30)
    
    if not correlation.empty:
        print(correlation.to_string())
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
