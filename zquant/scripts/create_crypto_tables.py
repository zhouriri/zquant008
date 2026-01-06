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
创建加密货币相关表
"""

from zquant.database import engine
from zquant.models.crypto import (
    CryptoPair,
    CryptoTicker,
    CryptoOrderBook,
    CryptoFundingRate,
    CryptoFavorite,
    CryptoPosition,
    CryptoTransaction,
    ExchangeConfig,
)


def create_crypto_tables():
    """创建所有加密货币相关表"""
    
    print("开始创建加密货币相关表...")
    
    try:
        # 创建基础表
        tables = [
            CryptoPair,
            CryptoTicker,
            CryptoOrderBook,
            CryptoFundingRate,
            CryptoFavorite,
            CryptoPosition,
            CryptoTransaction,
            ExchangeConfig,
        ]
        
        for table in tables:
            table.__table__.create(engine, checkfirst=True)
            print(f"✓ 创建表: {table.__tablename__}")
        
        # 创建K线表(常用周期)
        intervals = ["1h", "4h", "1d"]
        
        from zquant.models.crypto import create_kline_table_class, get_kline_table_name
        
        for interval in intervals:
            KlineTable = create_kline_table_class(interval)
            KlineTable.__table__.create(engine, checkfirst=True)
            print(f"✓ 创建K线表: {get_kline_table_name(interval)}")
        
        print("\n所有表创建成功!")
        
    except Exception as e:
        print(f"\n创建表失败: {e}")
        raise


if __name__ == "__main__":
    create_crypto_tables()
