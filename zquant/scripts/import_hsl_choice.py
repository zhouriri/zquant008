"""
从 CSV 文件导入 ZQ精选数据
支持原始情绪数据 (D/M/YYYY 格式) 和 标准格式 (YYYY-MM-DD)
使用方法: python zquant/scripts/import_hsl_choice.py todo/hsl_choice.csv
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
from sqlalchemy import text, func
from sqlalchemy.dialects.mysql import insert as mysql_insert

from zquant.database import SessionLocal
from zquant.models.data import HslChoice, Tustock

def import_csv_to_db(csv_path: str):
    if not Path(csv_path).exists():
        logger.error(f"找不到文件: {csv_path}")
        return

    db = SessionLocal()
    try:
        # 1. 获取所有股票信息 (symbol -> (ts_code, name))
        logger.info("正在加载股票代码映射信息...")
        stocks = db.query(Tustock.symbol, Tustock.ts_code, Tustock.name).all()
        stock_map = {s.symbol: (s.ts_code, s.name) for s in stocks}

        # 2. 读取 CSV 数据
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 兼容原始文件 'date' 和 转换后文件 'trade_date'
                raw_date = row.get('trade_date') or row.get('date')
                code_val = row.get('code')
                
                if not raw_date or not code_val:
                    continue
                
                code_val = code_val.strip()
                # 尝试通过 6 位代码查找标准的 ts_code 和名称
                stock_info = stock_map.get(code_val)
                
                if stock_info:
                    ts_code, name = stock_info
                else:
                    # 如果找不到，则根据规则推断 ts_code
                    if code_val.startswith('6'):
                        ts_code = f"{code_val}.SH"
                    elif code_val.startswith('0') or code_val.startswith('3'):
                        ts_code = f"{code_val}.SZ"
                    elif code_val.startswith('8') or code_val.startswith('4'):
                        ts_code = f"{code_val}.BJ"
                    else:
                        ts_code = code_val
                    name = None

                # 转换日期：支持 YYYY-MM-DD 和 D/M/YYYY
                trade_date = None
                for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                    try:
                        trade_date = datetime.strptime(raw_date.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
                
                if not trade_date:
                    logger.warning(f"数据行日期格式无法解析，跳过: {raw_date}")
                    continue

                records.append({
                    "trade_date": trade_date,
                    "ts_code": ts_code,
                    "code": code_val,
                    "name": name,
                    "created_by": "admin",
                    "updated_by": "admin",
                })

        if not records:
            logger.warning("没有可导入的数据记录")
            return

        # 3. 批量写入数据库
        logger.info(f"正在导入 {len(records)} 条数据到 zq_data_hsl_choice...")
        
        # 分批处理
        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            stmt = mysql_insert(HslChoice).values(batch)
            stmt = stmt.on_duplicate_key_update(
                name=stmt.inserted.name,
                code=stmt.inserted.code,
                updated_by=stmt.inserted.updated_by,
                updated_time=func.now(),
            )
            db.execute(stmt)
        
        db.commit()
        logger.info(f"成功导入 {len(records)} 条数据到 zq_data_hsl_choice")

    except Exception as e:
        db.rollback()
        logger.error(f"导入失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        # 默认尝试从 todo/hsl_choice.csv 导入，找不到再尝试当前目录
        p1 = Path("todo/hsl_choice.csv")
        path = str(p1) if p1.exists() else "hsl_choice.csv"
    
    import_csv_to_db(path)
