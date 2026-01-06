#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密货币快速启动脚本
一键完成初始化和数据同步
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy.orm import Session

from zquant.common.database import get_db
from zquant.data.crypto_sync import CryptoDataSync
from zquant.crypto.exchange_factory import ExchangeFactory


async def quick_start():
    """快速启动加密货币模块"""
    
    print("=" * 60)
    print("ZQuant 加密货币模块 - 快速启动")
    print("=" * 60)
    
    # 1. 检查交易所配置
    print("\n[1/5] 检查交易所配置...")
    try:
        binance = ExchangeFactory.create_exchange("binance")
        logger.info("✓ Binance交易所连接正常")
    except Exception as e:
        logger.warning(f"✗ Binance交易所连接失败: {e}")
        logger.info("提示: 请在.env文件中配置BINANCE_API_KEY和BINANCE_API_SECRET")
    
    # 2. 初始化数据库
    print("\n[2/5] 初始化数据库表...")
    try:
        from zquant.scripts.create_crypto_tables import create_all_tables
        create_all_tables()
        logger.info("✓ 数据库表创建成功")
    except Exception as e:
        logger.warning(f"✗ 数据库表创建失败: {e}")
    
    # 3. 同步交易对列表
    print("\n[3/5] 同步交易对列表...")
    try:
        sync = CryptoDataSync()
        pairs = await sync.sync_pairs()
        logger.info(f"✓ 同步了 {len(pairs)} 个交易对")
    except Exception as e:
        logger.warning(f"✗ 交易对同步失败: {e}")
    
    # 4. 同步热门交易对K线数据
    print("\n[4/5] 同步热门交易对K线数据...")
    try:
        sync = CryptoDataSync()
        hot_pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
        
        for pair in hot_pairs:
            try:
                await sync.sync_klines(pair, "1d", force=True)
                logger.info(f"  ✓ {pair} 1d K线同步成功")
            except Exception as e:
                logger.warning(f"  ✗ {pair} K线同步失败: {e}")
    except Exception as e:
        logger.warning(f"✗ K线数据同步失败: {e}")
    
    # 5. 获取实时行情
    print("\n[5/5] 获取实时行情...")
    try:
        ticker = await binance.get_ticker("BTCUSDT")
        logger.info(f"✓ BTC/USDT 价格: {ticker['price']}")
    except Exception as e:
        logger.warning(f"✗ 实时行情获取失败: {e}")
    
    print("\n" + "=" * 60)
    print("快速启动完成!")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 启动API服务: python -m zquant.main")
    print("  2. 启动前端服务: cd web && npm run dev")
    print("  3. 访问: http://localhost:8000/crypto/market")
    print("\n提示:")
    print("  - 运行 python zquant/scripts/init_crypto_scheduler.py 初始化定时任务")
    print("  - 查看 CRYPTO_FINAL_SUMMARY.md 了解详细使用说明")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(quick_start())
