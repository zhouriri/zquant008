"""
测试保存选股结果功能
"""
import sys
import os
from datetime import date

sys.path.append(os.getcwd())

from zquant.services.stock_filter import StockFilterService
from zquant.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_save_filter_results():
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 测试参数
        trade_date = date(2025, 12, 19)
        strategy_id = 1
        strategy_name = "测试策略"
        ts_codes = ["000001.SZ", "000002.SZ", "600000.SH"]
        
        print(f"测试保存选股结果...")
        print(f"交易日期: {trade_date}")
        print(f"策略ID: {strategy_id}")
        print(f"股票代码: {ts_codes}")
        
        # 调用保存方法
        saved_count = StockFilterService.save_filter_results(
            db=db,
            trade_date=trade_date,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            ts_codes=ts_codes,
            username="test_user"
        )
        
        print(f"\n保存成功! 保存了 {saved_count} 条记录")
        
        # 再次保存相同数据，测试重复处理
        print(f"\n测试重复保存...")
        saved_count2 = StockFilterService.save_filter_results(
            db=db,
            trade_date=trade_date,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            ts_codes=ts_codes,
            username="test_user"
        )
        print(f"第二次保存: {saved_count2} 条记录 (应该更新现有记录)")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_save_filter_results()
