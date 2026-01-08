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
#
# Author: kevin
# Contact:
#     - Email: kevin@vip.qq.com
#     - Wechat: zquant2025
#     - Issues: https://github.com/yoyoung/zquant/issues
#     - Documentation: https://github.com/yoyoung/zquant/blob/main/README.md
#     - Repository: https://github.com/yoyoung/zquant

from datetime import date
from typing import Any, Tuple, List, Optional

from loguru import logger
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert

from zquant.core.exceptions import ValidationError
from zquant.models.data import (
    HslChoice, 
    TUSTOCK_DAILY_BASIC_VIEW_NAME, 
    TUSTOCK_DAILY_VIEW_NAME
)


class HslChoiceService:
    """ZQ精选数据服务"""

    @staticmethod
    def query_hsl_choice(
        db: Session,
        trade_date_start: Optional[date] = None,
        trade_date_end: Optional[date] = None,
        ts_code: Optional[str] = None,
        code: Optional[str] = None,
        name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[list[dict[str, Any]], int]:
        """
        查询ZQ精选数据

        Args:
            db: 数据库会话
            trade_date_start: 开始日期
            trade_date_end: 结束日期
            ts_code: TS代码
            code: 股票代码
            name: 股票名称
            skip: 跳过记录数
            limit: 每页记录数

        Returns:
            (结果列表, 总数)
        """
        # 构建基础查询
        select_columns = """
        h.id, h.trade_date, h.ts_code, h.code,
        COALESCE(h.name, sb.name) as name,
        h.created_by, h.created_time, h.updated_by, h.updated_time
        """

        where_clauses = []
        params = {"limit": limit, "skip": skip}

        if trade_date_start:
            where_clauses.append("h.trade_date >= :start_date")
            params["start_date"] = trade_date_start
        
        if trade_date_end:
            where_clauses.append("h.trade_date <= :end_date")
            params["end_date"] = trade_date_end
            
        if ts_code:
            where_clauses.append("h.ts_code = :ts_code")
            params["ts_code"] = ts_code

        if code:
            where_clauses.append("h.code = :code")
            params["code"] = code

        if name:
            where_clauses.append("COALESCE(h.name, sb.name) LIKE :name")
            params["name"] = f"%{name}%"

        where_str = " AND ".join(where_clauses) if where_clauses else "1=1"

        # 构建SQL
        sql = f"""
        SELECT {select_columns}, COUNT(*) OVER() AS total_count
        FROM `zq_data_hsl_choice` h
        LEFT JOIN `zq_data_tustock_stockbasic` sb ON h.ts_code = sb.ts_code
        WHERE {where_str}
        ORDER BY h.trade_date DESC, h.ts_code ASC
        LIMIT :limit OFFSET :skip
        """

        try:
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            columns = list(result.keys())

            items = []
            total = 0

            # 找到 total_count 列的索引
            total_count_idx = -1
            try:
                total_count_idx = columns.index("total_count")
            except ValueError:
                pass

            for row_idx, row in enumerate(rows):
                item = {}
                for col_idx, col in enumerate(columns):
                    if col_idx == total_count_idx:
                        if row_idx == 0:
                            total = row[col_idx]
                        continue
                    item[col] = row[col_idx]
                items.append(item)

            return items, total

        except Exception as e:
            logger.error(f"查询ZQ精选数据失败: {e}")
            raise ValidationError(f"查询失败: {str(e)}")

    @staticmethod
    def add_hsl_choice(
        db: Session,
        trade_date: date,
        ts_codes: List[str],
        username: Optional[str] = None,
    ) -> int:
        """
        添加ZQ精选数据

        Args:
            db: 数据库会话
            trade_date: 交易日期
            ts_codes: 股票代码列表
            username: 操作用户

        Returns:
            新增记录数
        """
        if not ts_codes:
            return 0

        try:
            # 批量获取股票名称
            name_map = {}
            if ts_codes:
                clean_codes = [c.strip() for c in ts_codes if c.strip()]
                if clean_codes:
                    name_sql = text("SELECT ts_code, name FROM `zq_data_tustock_stockbasic` WHERE ts_code IN :codes")
                    name_result = db.execute(name_sql, {"codes": clean_codes})
                    name_map = {row[0]: row[1] for row in name_result.fetchall()}

            records = []
            for ts_code in ts_codes:
                if not ts_code.strip():
                    continue
                
                clean_ts_code = ts_code.strip()
                # 提取股票代码（通常是前6位）
                code = clean_ts_code.split('.')[0] if '.' in clean_ts_code else clean_ts_code[:6]
                name = name_map.get(clean_ts_code)
                
                records.append({
                    "trade_date": trade_date,
                    "ts_code": clean_ts_code,
                    "code": code,
                    "name": name,
                    "created_by": username,
                    "updated_by": username,
                })

            if not records:
                return 0

            # 使用 INSERT IGNORE ... ON DUPLICATE KEY UPDATE
            stmt = mysql_insert(HslChoice).values(records)
            stmt = stmt.on_duplicate_key_update(
                name=stmt.inserted.name,
                updated_by=stmt.inserted.updated_by,
                updated_time=func.now(),
            )

            result = db.execute(stmt)
            db.commit()
            
            return result.rowcount

        except Exception as e:
            db.rollback()
            logger.error(f"添加ZQ精选数据失败: {e}")
            raise ValidationError(f"添加失败: {str(e)}")
