"""
使用 CSV 数据更新 zq_data_tustock_stockbasic 表中的缺失值
使用方法: python zquant/scripts/update_stock_basic_from_csv.py todo/cn_tustock.csv
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

# 设置项目根目录
script_dir = Path(__file__).resolve().parent  # zquant/scripts
zquant_dir = script_dir.parent  # zquant 目录
project_root = zquant_dir.parent  # 项目根目录
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import text, func, or_, String
from sqlalchemy.dialects.mysql import insert as mysql_insert

from zquant.database import SessionLocal
from zquant.models.data import Tustock

def parse_date(date_str):
    if not date_str or date_str.lower() == 'nan' or date_str == '':
        return None
    # 兼容 D/M/YYYY 格式
    try:
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
    except ValueError:
        # 尝试其他格式
        for fmt in ('%Y-%m-%d', '%Y%m%d', '%d/%m/%Y %H:%M:%S'):
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
    return None

def update_stock_basic(csv_path: str):
    if not Path(csv_path).exists():
        logger.error(f"找不到文件: {csv_path}")
        return

    db = SessionLocal()
    try:
        logger.info(f"正在读取 CSV 文件: {csv_path}")
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts_code = row.get('ts_code')
                if not ts_code:
                    continue
                
                # 转换日期字段
                list_date = parse_date(row.get('list_date'))
                delist_date = parse_date(row.get('delist_date'))

                record = {
                    "ts_code": ts_code,
                    "symbol": row.get('symbol'),
                    "name": row.get('name'),
                    "area": row.get('area'),
                    "industry": row.get('industry'),
                    "fullname": row.get('fullname'),
                    "enname": row.get('enname'),
                    "cnspell": row.get('cnspell'),
                    "market": row.get('market'),
                    "exchange": row.get('exchange'),
                    "curr_type": row.get('curr_type'),
                    "list_status": row.get('list_status'),
                    "list_date": list_date,
                    "delist_date": delist_date,
                    "is_hs": row.get('is_hs'),
                    "act_name": row.get('act_name'),
                    "act_ent_type": row.get('act_ent_type'),
                    "updated_by": "csv_update",
                }
                # 过滤掉 None 值，避免覆盖已有数据（如果 CSV 里是空的）
                # 但根据需求，我们是想用 CSV 里的非空值去补全数据库里的空值
                records.append(record)

        if not records:
            logger.warning("没有可更新的数据记录")
            return

        logger.info(f"开始更新 {len(records)} 条记录到 zq_data_tustock_stockbasic...")
        
        # 分批处理以提高性能
        batch_size = 500
        updated_count = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            stmt = mysql_insert(Tustock).values(batch)
            
            # 使用 ON DUPLICATE KEY UPDATE 逻辑
            # 为了实现“更新缺失值”，我们只在原值为 NULL 或空字符串时更新
            update_cols = {}
            for col_name in record.keys():
                if col_name == 'ts_code':
                    continue
                
                col_obj = getattr(Tustock, col_name)
                # 使用 func.values() 明确生成 VALUES(col) 语法，避免被渲染为错误的 new.col
                inserted_val = func.values(col_obj)
                
                # 针对不同类型采取不同的空值判断逻辑
                if isinstance(col_obj.type, String):
                    cond = or_(col_obj.is_(None), col_obj == '')
                else:
                    cond = col_obj.is_(None)
                    
                update_cols[col_name] = func.if_(
                    cond,
                    inserted_val,
                    col_obj
                )
            
            # 始终更新修改时间和修改人
            update_cols['updated_time'] = func.now()
            update_cols['updated_by'] = 'csv_update'
            
            stmt = stmt.on_duplicate_key_update(update_cols)
            db.execute(stmt)
            updated_count += len(batch)
            logger.info(f"已处理 {updated_count}/{len(records)} 条记录")
        
        db.commit()
        logger.info("数据更新完成！")

    except Exception as e:
        db.rollback()
        logger.error(f"更新失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "todo/cn_tustock.csv"
    update_stock_basic(path)

