
import sys
import os
from datetime import date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# 增加路径
sys.path.append(os.getcwd())

from zquant.services.stock_filter import StockFilterService
from zquant.config import settings

def test_strategy_api():
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 获取最新的交易日期或指定一个（假设有数据）
        # 这里为了演示，随便写一个日期和策略ID
        # 实际测试时需要确保数据库中有对应的 zq_quant_stock_filter_result 数据
        trade_date = date(2025, 12, 19) 
        strategy_id = 1
        
        print(f"Testing Strategy Stock Results for Date: {trade_date}, Strategy ID: {strategy_id}")
        
        items, total = StockFilterService.get_strategy_stock_results(
            db=db,
            trade_date=trade_date,
            strategy_id=strategy_id,
            limit=5
        )
        
        print(f"Total Results: {total}")
        for item in items:
            print(f"Stock: {item.get('ts_code')} - {item.get('name')}, Close: {item.get('db_close')}, PE: {item.get('pe')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_strategy_api()
