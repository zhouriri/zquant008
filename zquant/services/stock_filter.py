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

"""
量化选股服务层
"""

import json
from datetime import date
from typing import Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from zquant.core.exceptions import NotFoundError, ValidationError
from zquant.data.storage_base import log_sql_statement
from zquant.models.data import (
    StockFilterStrategy,
    TUSTOCK_DAILY_BASIC_VIEW_NAME,
    TUSTOCK_DAILY_VIEW_NAME,
    TUSTOCK_FACTOR_VIEW_NAME,
    StockFilterResult,
    Tustock,
)


class StockFilterService:
    """量化选股服务"""

    # 字段到表别名的映射，用于解决 SQL 模糊性并支持自动前缀
    COLUMN_MAP = {
        # 基础信息 (sb)
        "ts_code": "sb.ts_code",
        "symbol": "sb.symbol",
        "name": "sb.name",
        "industry": "sb.industry",
        "area": "sb.area",
        "market": "sb.market",
        "exchange": "sb.exchange",
        "fullname": "sb.fullname",
        "enname": "sb.enname",
        "cnspell": "sb.cnspell",
        "curr_type": "sb.curr_type",
        "list_status": "sb.list_status",
        "list_date": "sb.list_date",
        "delist_date": "sb.delist_date",
        "is_hs": "sb.is_hs",
        "act_name": "sb.act_name",
        "act_ent_type": "sb.act_ent_type",
        # 每日指标 (db)
        "db_close": "db.close",
        "turnover_rate": "db.turnover_rate",
        "turnover_rate_f": "db.turnover_rate_f",
        "volume_ratio": "db.volume_ratio",
        "pe": "db.pe",
        "pe_ttm": "db.pe_ttm",
        "pb": "db.pb",
        "ps": "db.ps",
        "ps_ttm": "db.ps_ttm",
        "dv_ratio": "db.dv_ratio",
        "dv_ttm": "db.dv_ttm",
        "total_share": "db.total_share",
        "float_share": "db.float_share",
        "free_share": "db.free_share",
        "total_mv": "db.total_mv",
        "circ_mv": "db.circ_mv",
        # 日线数据 (dd)
        "dd_open": "dd.open",
        "dd_high": "dd.high",
        "dd_low": "dd.low",
        "dd_close": "dd.close",
        "dd_pre_close": "dd.pre_close",
        "dd_change": "dd.change",
        "pct_chg": "dd.pct_chg",
        "dd_vol": "dd.vol",
        "amount": "dd.amount",
        # 技术因子 (f)
        "adj_factor": "f.adj_factor",
        "open_hfq": "f.open_hfq",
        "open_qfq": "f.open_qfq",
        "close_hfq": "f.close_hfq",
        "close_qfq": "f.close_qfq",
        "high_hfq": "f.high_hfq",
        "high_qfq": "f.high_qfq",
        "low_hfq": "f.low_hfq",
        "low_qfq": "f.low_qfq",
        "pre_close_hfq": "f.pre_close_hfq",
        "pre_close_qfq": "f.pre_close_qfq",
        "macd_dif": "f.macd_dif",
        "macd_dea": "f.macd_dea",
        "macd": "f.macd",
        "kdj_k": "f.kdj_k",
        "kdj_d": "f.kdj_d",
        "kdj_j": "f.kdj_j",
        "rsi_6": "f.rsi_6",
        "rsi_12": "f.rsi_12",
        "rsi_24": "f.rsi_24",
        "boll_upper": "f.boll_upper",
        "boll_mid": "f.boll_mid",
        "boll_lower": "f.boll_lower",
        "cci": "f.cci",
    }

    # 字段转换因子 (用于在过滤时将输入或策略中的“亿”单位数值转换为数据库原生单位)
    UNIT_FACTORS = {
        "total_mv": 10000.0,      # 万元 -> 亿
        "circ_mv": 10000.0,       # 万元 -> 亿
        "amount": 100000.0,       # 千元 -> 亿
        "total_share": 10000.0,   # 万股 -> 亿股
        "float_share": 10000.0,   # 万股 -> 亿股
        "free_share": 10000.0,    # 万股 -> 亿股
    }

    @classmethod
    def _validate_field_name(cls, field: str) -> bool:
        """
        验证字段名是否安全（防止SQL注入）
        
        只允许字母、数字、下划线，且不能为空
        """
        if not field or not isinstance(field, str):
            return False
        # 只允许字母、数字、下划线，长度限制在1-64之间
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$', field))
    
    @classmethod
    def _get_full_field_name(cls, field: str, use_mapping: bool = True, table_alias: str | None = None) -> str:
        """
        获取完全限定的字段名
        
        安全措施：
        1. 验证字段名格式（防止SQL注入）
        2. 使用白名单映射
        3. 对于动态字段，使用参数化查询
        """
        # 验证字段名安全性
        if not cls._validate_field_name(field):
            raise ValidationError(f"无效的字段名: {field}")
        
        # 如果不使用映射（用于扁平查询结果表），直接返回别名前缀的字段名
        if not use_mapping and table_alias:
            return f"{table_alias}.`{field}`"
        
        if field in cls.COLUMN_MAP:
            full_name = cls.COLUMN_MAP[field]
            # 如果包含空格（如 "db.close AS db_close"），只取前面的部分
            if " " in full_name:
                return full_name.split(" ")[0]
            return full_name
        
        # 如果不在映射中，默认尝试从因子表 (f) 查询
        # 因子表和专业因子表可能有很多动态列
        # 使用反引号包裹字段名，并确保字段名已通过验证
        prefix = f"{table_alias}." if table_alias else "f."
        return f"{prefix}`{field}`"

    @classmethod
    def _build_single_condition(cls, condition: dict[str, Any], param_index: int, use_mapping: bool = True, table_alias: str | None = None) -> tuple[str, dict[str, Any], int]:
        """
        构建单个条件的SQL

        Args:
            condition: 条件字典，格式：{"field": "pe", "operator": "<", "value": 20, "not": False}
            param_index: 参数索引
            use_mapping: 是否使用字段映射（False表示直接使用字段名）
            table_alias: 表别名

        Returns:
            (SQL条件片段, 参数字典, 新s参数索引)
        """
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        not_operator = condition.get("not", False) or condition.get("not_", False)

        if not field or operator is None:
            return "", {}, param_index

        full_field = StockFilterService._get_full_field_name(field, use_mapping=use_mapping, table_alias=table_alias)
        param_name = f"filter_{param_index}"
        param_index += 1
        params = {}

        # 单位缩放：如果字段在 UNIT_FACTORS 中，将输入的“亿”单位数值转换为数据库原生单位
        factor = cls.UNIT_FACTORS.get(field)
        adj_value = value
        if factor is not None and value is not None:
            try:
                if isinstance(value, (int, float)):
                    adj_value = float(value) * factor
                elif isinstance(value, str) and value.strip():
                    # 前端 Input 传过来的是字符串，需要先转为数字再进行单位缩放
                    adj_value = float(value.strip()) * factor
                elif isinstance(value, list):
                    adj_value = []
                    for v in value:
                        if isinstance(v, (int, float)):
                            adj_value.append(float(v) * factor)
                        elif isinstance(v, str) and v.strip():
                            adj_value.append(float(v.strip()) * factor)
                        else:
                            adj_value.append(v)
            except (ValueError, TypeError):
                # 如果转换失败，保持原样（交由数据库报错或处理）
                logger.warning(f"无法将值转换为数字进行单位缩放: field={field}, value={value}")
                adj_value = value

        # 构建基础SQL条件
        base_sql = ""
        if operator == "=":
            base_sql = f"{full_field} = :{param_name}"
            params[param_name] = adj_value
        elif operator == "!=":
            base_sql = f"{full_field} != :{param_name}"
            params[param_name] = adj_value
        elif operator == ">":
            base_sql = f"{full_field} > :{param_name}"
            params[param_name] = adj_value
        elif operator == "<":
            base_sql = f"{full_field} < :{param_name}"
            params[param_name] = adj_value
        elif operator == ">=":
            base_sql = f"{full_field} >= :{param_name}"
            params[param_name] = adj_value
        elif operator == "<=":
            base_sql = f"{full_field} <= :{param_name}"
            params[param_name] = adj_value
        elif operator == "LIKE":
            base_sql = f"{full_field} LIKE :{param_name}"
            params[param_name] = f"%{adj_value}%"
        elif operator == "IN":
            if isinstance(adj_value, list):
                if not adj_value:
                    base_sql = "1=0" # 空列表永远为假
                else:
                    placeholders = ", ".join([f":{param_name}_{i}" for i in range(len(adj_value))])
                    base_sql = f"{full_field} IN ({placeholders})"
                    for i, v in enumerate(adj_value):
                        params[f"{param_name}_{i}"] = v
            else:
                base_sql = f"{full_field} = :{param_name}"
                params[param_name] = adj_value
        elif operator == "BETWEEN":
            if isinstance(adj_value, list) and len(adj_value) == 2:
                base_sql = f"{full_field} BETWEEN :{param_name}_min AND :{param_name}_max"
                params[f"{param_name}_min"] = adj_value[0]
                params[f"{param_name}_max"] = adj_value[1]
            else:
                logger.warning(f"BETWEEN操作符需要两个值，跳过条件: {field}")
                return "", {}, param_index - 1
        elif operator.upper() == "IS":
            if str(value).upper() == "NULL":
                base_sql = f"{full_field} IS NULL"
            elif str(value).upper() == "NOT NULL":
                base_sql = f"{full_field} IS NOT NULL"
            param_index -= 1 # IS NULL 不需要参数
        elif operator.upper() == "IS NULL":
            base_sql = f"{full_field} IS NULL"
            param_index -= 1
        elif operator.upper() == "IS NOT NULL":
            base_sql = f"{full_field} IS NOT NULL"
            param_index -= 1

        # 应用NOT运算符
        if not_operator and base_sql:
            base_sql = f"NOT ({base_sql})"

        return base_sql, params, param_index

    @staticmethod
    def _build_filter_conditions_recursive(
        filter_conditions: dict[str, Any] | list[dict[str, Any]], param_index: int = 0, use_mapping: bool = True, table_alias: str | None = None
    ) -> tuple[str, dict[str, Any], int]:
        """
        递归构建筛选条件SQL（支持逻辑组合）

        Args:
            filter_conditions: 筛选条件，可以是：
                - 列表格式（向后兼容）：[{"field": "pe", "operator": "<", "value": 20}, ...]
                - 逻辑组格式：{"logic": "AND", "conditions": [...], "not": False}
            param_index: 参数索引起始值
            use_mapping: 是否使用字段映射
            table_alias: 表别名

        Returns:
            (WHERE子句, 参数字典, 新的参数索引)
        """
        if not filter_conditions:
            return "1=1", {}, param_index

        # 处理旧格式：简单条件列表（向后兼容）
        if isinstance(filter_conditions, list):
            if not filter_conditions:
                return "1=1", {}, param_index

            conditions = []
            all_params = {}
            current_param_index = param_index

            for condition in filter_conditions:
                # 统一调用递归方法，以便支持列表中的嵌套逻辑组
                sql, params, current_param_index = StockFilterService._build_filter_conditions_recursive(
                    condition, current_param_index, use_mapping=use_mapping, table_alias=table_alias
                )
                if sql and sql != "1=1":
                    conditions.append(f"({sql})")
                    all_params.update(params)

            if not conditions:
                return "1=1", {}, param_index

            where_clause = " AND ".join(conditions)
            return where_clause, all_params, current_param_index

        # 处理新格式：逻辑组 或 单个条件字典
        if isinstance(filter_conditions, dict):
            # 如果包含 field，说明是单个条件，直接调用 _build_single_condition
            if "field" in filter_conditions:
                # 检查是否是有效的单个条件（有 field 且有 operator）
                if filter_conditions.get("field") and filter_conditions.get("operator"):
                    return StockFilterService._build_single_condition(filter_conditions, param_index, use_mapping=use_mapping, table_alias=table_alias)
                else:
                    return "1=1", {}, param_index

            logic = filter_conditions.get("logic", "AND").upper()
            conditions_list = filter_conditions.get("conditions", [])
            not_operator = filter_conditions.get("not", False) or filter_conditions.get("not_", False)

            if not conditions_list:
                return "1=1", {}, param_index

            # 递归处理每个条件
            condition_sqls = []
            all_params = {}
            current_param_index = param_index

            for condition in conditions_list:
                sql, params, current_param_index = StockFilterService._build_filter_conditions_recursive(
                    condition, current_param_index, use_mapping=use_mapping, table_alias=table_alias
                )
                if sql and sql != "1=1":
                    condition_sqls.append(f"({sql})")
                    all_params.update(params)

            if not condition_sqls:
                return "1=1", {}, param_index

            # 使用逻辑运算符连接条件
            if logic == "OR":
                where_clause = " OR ".join(condition_sqls)
            else:  # 默认使用AND
                where_clause = " AND ".join(condition_sqls)

            # 应用NOT运算符
            if not_operator:
                where_clause = f"NOT ({where_clause})"

            return where_clause, all_params, current_param_index

        return "1=1", {}, param_index

    @staticmethod
    def _build_filter_conditions(filter_conditions: dict[str, Any] | list[dict[str, Any]] | None, use_mapping: bool = True, table_alias: str | None = None) -> tuple[str, dict[str, Any]]:
        """
        构建筛选条件SQL（入口方法）

        Args:
            filter_conditions: 筛选条件，支持：
                - None: 无条件
                - 列表格式（向后兼容）：[{"field": "pe", "operator": "<", "value": 20}, ...]
                - 逻辑组格式：{"logic": "AND", "conditions": [...], "not": False}
            use_mapping: 是否使用字段映射
            table_alias: 表别名

        Returns:
            (WHERE子句, 参数字典)
        """
        if not filter_conditions:
            return "1=1", {}

        where_clause, params, _ = StockFilterService._build_filter_conditions_recursive(filter_conditions, use_mapping=use_mapping, table_alias=table_alias)
        return where_clause, params

    @staticmethod
    def _build_order_by(sort_config: list[dict[str, str]] | None, table_alias: str = "sb", use_mapping: bool = True) -> str:
        """
        构建排序SQL

        Args:
            sort_config: 排序配置列表，格式：[{"field": "pe", "order": "asc"}, ...]
            table_alias: 默认表别名，用于 ts_code 排序
            use_mapping: 是否使用字段映射

        Returns:
            ORDER BY子句
        """
        if not sort_config:
            return f"ORDER BY {table_alias}.ts_code ASC"

        order_parts = []
        for sort_item in sort_config:
            field = sort_item.get("field")
            order = sort_item.get("order", "asc").upper()

            if not field:
                continue

            if order not in ["ASC", "DESC"]:
                order = "ASC"

            full_field = StockFilterService._get_full_field_name(field, use_mapping=use_mapping, table_alias=table_alias)
            order_parts.append(f"{full_field} {order}")

        if order_parts:
            return "ORDER BY " + ", ".join(order_parts)
        else:
            return f"ORDER BY {table_alias}.ts_code ASC"

    @classmethod
    def _build_select_columns(cls, selected_columns: list[str] | None) -> str:
        """
        构建SELECT列

        Args:
            selected_columns: 选中的列列表

        Returns:
            SELECT子句
        """
        if not selected_columns:
            # 默认选择所有常用列（包括基础信息、每日指标、日线数据和常用因子）
            from zquant.models.data import StockFilterResult
            # 获取模型中定义的反范式化列（排除 id, strategy_id 等策略相关列）
            exclude_cols = ["id", "strategy_id", "strategy_name", "created_by", "created_time", "updated_by", "updated_time", "trade_date", "ts_code"]
            model_cols = [c.name for c in StockFilterResult.__table__.columns if c.name not in exclude_cols]
            
            # 使用 COLUMN_MAP 构建带别名的 SELECT 子句
            select_parts = ["sb.ts_code"]
            for col in model_cols:
                if col in cls.COLUMN_MAP:
                    mapping = cls.COLUMN_MAP[col]
                    if "." in mapping and mapping.split(".")[1] != col:
                        select_parts.append(f"{mapping} AS {col}")
                    else:
                        select_parts.append(mapping)
                else:
                    # 如果不在映射中，默认从因子视图查询
                    select_parts.append(f"f.`{col}` AS `{col}`")
            
            return ", ".join(select_parts)

        select_parts = []
        for col in selected_columns:
            if col in cls.COLUMN_MAP:
                mapping = cls.COLUMN_MAP[col]
                if " AS " not in mapping.upper() and mapping != col:
                    # 只有在 mapping 不包含 AS 且 mapping 名字与 col 不一致时才添加别名
                    # 但为了统一，我们查一下 map 中是否有 alias 需求
                    # 比如 db.close AS db_close
                    if "." in mapping and mapping.split(".")[1] != col:
                        select_parts.append(f"{mapping} AS {col}")
                    else:
                        select_parts.append(mapping)
                else:
                    select_parts.append(mapping)
            else:
                # 如果不在映射中，尝试直接使用（可能是因子列）
                select_parts.append(f"f.`{col}` AS `{col}`")

        if not select_parts:
            return "sb.ts_code, sb.symbol, sb.name"

        return ", ".join(select_parts)

    @staticmethod
    def get_filter_results(
        db: Session,
        trade_date: date,
        filter_conditions: list[dict[str, Any]] | None = None,
        selected_columns: list[str] | None = None,
        sort_config: list[dict[str, str]] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取选股结果

        Args:
            db: 数据库会话
            trade_date: 交易日期
            filter_conditions: 筛选条件列表
            selected_columns: 选中的列列表
            sort_config: 排序配置列表
            skip: 跳过记录数
            limit: 每页记录数

        Returns:
            (结果列表, 总数)
        """
        try:
            # 构建WHERE条件
            where_clause, where_params = StockFilterService._build_filter_conditions(filter_conditions)

            # 构建SELECT列
            select_columns = StockFilterService._build_select_columns(selected_columns)

            # 构建ORDER BY
            order_by = StockFilterService._build_order_by(sort_config)

            # 构建SQL查询（使用窗口函数一次性获取数据和总数）
            sql = f"""
            SELECT :trade_date AS trade_date, {select_columns}, COUNT(*) OVER() AS total_count
            FROM `zq_data_tustock_stockbasic` sb
            LEFT JOIN `{TUSTOCK_DAILY_BASIC_VIEW_NAME}` db 
                ON sb.ts_code = db.ts_code AND db.trade_date = :trade_date
            LEFT JOIN `{TUSTOCK_DAILY_VIEW_NAME}` dd 
                ON sb.ts_code = dd.ts_code AND dd.trade_date = :trade_date
            LEFT JOIN `{TUSTOCK_FACTOR_VIEW_NAME}` f 
                ON sb.ts_code = f.ts_code AND f.trade_date = :trade_date
            WHERE sb.delist_date IS NULL AND ({where_clause})
            {order_by}
            LIMIT :limit OFFSET :skip
            """

            # 合并参数
            params = {
                "trade_date": trade_date,
                "skip": skip,
                "limit": limit,
                **where_params,
            }

            # 打印SQL日志（INFO级别，确保同时输出到控制台和日志文件）
            log_sql_statement(sql, params)

            # 执行查询
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            columns = list(result.keys())  # 转换为列表以便索引

            # 转换为字典列表，并从第一行提取总数
            items = []
            total = 0
            
            # 找到total_count列的索引
            total_count_idx = None
            try:
                total_count_idx = columns.index("total_count")
            except ValueError:
                # 如果找不到total_count列，说明可能有问题，但继续处理
                logger.warning("未找到total_count列，可能影响总数统计")
            
            for row_idx, row in enumerate(rows):
                item = {}
                for col_idx, col in enumerate(columns):
                    # 跳过total_count字段
                    if col_idx == total_count_idx:
                        # 从第一行提取total_count（所有行的total_count值相同）
                        if row_idx == 0:
                            value = row[col_idx]
                            total = int(value) if value is not None else 0
                        continue
                    
                    value = row[col_idx]
                    
                    # 处理日期和数值类型
                    if hasattr(value, "isoformat"):
                        item[col] = value.isoformat()
                    elif isinstance(value, (int, float)) and value is not None:
                        item[col] = float(value)
                    else:
                        item[col] = value
                
                # 添加item（已排除total_count字段）
                items.append(item)

            # 如果查询结果为空，total应该为0
            if len(rows) == 0:
                total = 0

            return items, total

        except Exception as e:
            logger.error(f"获取选股结果失败: {e}")
            raise ValidationError(f"获取选股结果失败: {str(e)}")

    @staticmethod
    def get_available_columns(db: Session) -> dict[str, list[dict[str, Any]]]:
        """
        获取可用列列表

        Args:
            db: 数据库会话

        Returns:
            列信息字典，按表分组
        """
        columns_info = {
            "basic": [
                {"field": "trade_date", "label": "交易日期", "type": "date"},
                {"field": "ts_code", "label": "TS代码", "type": "string"},
                {"field": "symbol", "label": "股票代码", "type": "string"},
                {"field": "name", "label": "股票名称", "type": "string"},
                {"field": "industry", "label": "所属行业", "type": "string"},
                {"field": "area", "label": "地域", "type": "string"},
                {"field": "market", "label": "市场类型", "type": "string"},
                {"field": "exchange", "label": "交易所代码", "type": "string"},
                {"field": "fullname", "label": "股票全称", "type": "string"},
                {"field": "enname", "label": "英文全称", "type": "string"},
                {"field": "cnspell", "label": "拼音缩写", "type": "string"},
                {"field": "curr_type", "label": "交易货币", "type": "string"},
                {"field": "list_status", "label": "上市状态", "type": "string"},
                {"field": "list_date", "label": "上市日期", "type": "string"},
                {"field": "delist_date", "label": "退市日期", "type": "string"},
                {"field": "is_hs", "label": "是否沪深港通标的", "type": "string"},
                {"field": "act_name", "label": "实控人名称", "type": "string"},
                {"field": "act_ent_type", "label": "实控人企业性质", "type": "string"},
            ],
            "daily_basic": [
                {"field": "db_close", "label": "收盘价(指标)", "type": "number"},
                {"field": "turnover_rate", "label": "换手率", "type": "number"},
                {"field": "turnover_rate_f", "label": "换手率(自由流通股)", "type": "number"},
                {"field": "volume_ratio", "label": "量比", "type": "number"},
                {"field": "pe", "label": "市盈率", "type": "number"},
                {"field": "pe_ttm", "label": "市盈率TTM", "type": "number"},
                {"field": "pb", "label": "市净率", "type": "number"},
                {"field": "ps", "label": "市销率", "type": "number"},
                {"field": "ps_ttm", "label": "市销率TTM", "type": "number"},
                {"field": "dv_ratio", "label": "股息率", "type": "number"},
                {"field": "dv_ttm", "label": "股息率TTM", "type": "number"},
                {"field": "total_share", "label": "总股本", "type": "number"},
                {"field": "float_share", "label": "流通股本", "type": "number"},
                {"field": "free_share", "label": "自由流通股本", "type": "number"},
                {"field": "total_mv", "label": "总市值", "type": "number"},
                {"field": "circ_mv", "label": "流通市值", "type": "number"},
            ],
            "daily": [
                {"field": "dd_open", "label": "开盘价", "type": "number"},
                {"field": "dd_high", "label": "最高价", "type": "number"},
                {"field": "dd_low", "label": "最低价", "type": "number"},
                {"field": "dd_close", "label": "收盘价", "type": "number"},
                {"field": "dd_pre_close", "label": "昨收价", "type": "number"},
                {"field": "dd_change", "label": "涨跌额", "type": "number"},
                {"field": "pct_chg", "label": "涨跌幅", "type": "number"},
                {"field": "dd_vol", "label": "成交量", "type": "number"},
                {"field": "amount", "label": "成交额", "type": "number"},
            ],
            "factor": [
                {"field": "adj_factor", "label": "复权因子", "type": "number"},
                {"field": "open_hfq", "label": "开盘价后复权", "type": "number"},
                {"field": "open_qfq", "label": "开盘价前复权", "type": "number"},
                {"field": "close_hfq", "label": "收盘价后复权", "type": "number"},
                {"field": "close_qfq", "label": "收盘价前复权", "type": "number"},
                {"field": "high_hfq", "label": "最高价后复权", "type": "number"},
                {"field": "high_qfq", "label": "最高价前复权", "type": "number"},
                {"field": "low_hfq", "label": "最低价后复权", "type": "number"},
                {"field": "low_qfq", "label": "最低价前复权", "type": "number"},
                {"field": "pre_close_hfq", "label": "昨收价后复权", "type": "number"},
                {"field": "pre_close_qfq", "label": "昨收价前复权", "type": "number"},
                {"field": "macd_dif", "label": "MACD_DIF", "type": "number"},
                {"field": "macd_dea", "label": "MACD_DEA", "type": "number"},
                {"field": "macd", "label": "MACD", "type": "number"},
                {"field": "kdj_k", "label": "KDJ_K", "type": "number"},
                {"field": "kdj_d", "label": "KDJ_D", "type": "number"},
                {"field": "kdj_j", "label": "KDJ_J", "type": "number"},
                {"field": "rsi_6", "label": "RSI_6", "type": "number"},
                {"field": "rsi_12", "label": "RSI_12", "type": "number"},
                {"field": "rsi_24", "label": "RSI_24", "type": "number"},
                {"field": "boll_upper", "label": "BOLL_UPPER", "type": "number"},
                {"field": "boll_mid", "label": "BOLL_MID", "type": "number"},
                {"field": "boll_lower", "label": "BOLL_LOWER", "type": "number"},
                {"field": "cci", "label": "CCI", "type": "number"},
            ],
            "audit": [
                {"field": "strategy_name", "label": "策略名称", "type": "string"},
                {"field": "created_by", "label": "创建人", "type": "string"},
                {"field": "created_time", "label": "创建时间", "type": "datetime"},
                {"field": "updated_by", "label": "修改人", "type": "string"},
                {"field": "updated_time", "label": "修改时间", "type": "datetime"},
            ]
        }

        return columns_info

        return columns_info

    @staticmethod
    def save_strategy(
        db: Session,
        user_id: int,
        name: str,
        description: str | None = None,
        filter_conditions: list[dict[str, Any]] | None = None,
        selected_columns: list[str] | None = None,
        sort_config: list[dict[str, str]] | None = None,
        created_by: str | None = None,
    ) -> StockFilterStrategy:
        """
        保存策略模板

        Args:
            db: 数据库会话
            user_id: 用户ID
            name: 策略名称
            description: 策略描述
            filter_conditions: 筛选条件
            selected_columns: 选中列
            sort_config: 排序配置
            created_by: 创建人

        Returns:
            StockFilterStrategy: 保存的策略记录
        """
        # 检查是否已存在同名策略
        existing = (
            db.query(StockFilterStrategy)
            .filter(StockFilterStrategy.user_id == user_id, StockFilterStrategy.name == name)
            .first()
        )
        if existing:
            raise ValidationError(f"策略名称 {name} 已存在")

        # 创建策略记录
        strategy = StockFilterStrategy(
            user_id=user_id,
            name=name,
            description=description,
            filter_conditions=json.dumps(filter_conditions) if filter_conditions else None,
            selected_columns=json.dumps(selected_columns) if selected_columns else None,
            sort_config=json.dumps(sort_config) if sort_config else None,
            created_by=created_by,
            updated_by=created_by,  # 创建时 updated_by 和 created_by 一致
        )

        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        return strategy

    @staticmethod
    def get_strategies(db: Session, user_id: int) -> list[StockFilterStrategy]:
        """
        获取用户策略列表

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            策略列表
        """
        strategies = (
            db.query(StockFilterStrategy)
            .filter(StockFilterStrategy.user_id == user_id)
            .order_by(StockFilterStrategy.created_time.desc())
            .all()
        )
        return strategies

    @staticmethod
    def get_strategy_by_id(db: Session, strategy_id: int, user_id: int) -> StockFilterStrategy:
        """
        根据ID获取策略

        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID

        Returns:
            StockFilterStrategy: 策略记录

        Raises:
            NotFoundError: 策略不存在
        """
        strategy = (
            db.query(StockFilterStrategy)
            .filter(StockFilterStrategy.id == strategy_id, StockFilterStrategy.user_id == user_id)
            .first()
        )
        if not strategy:
            raise NotFoundError(f"策略 ID {strategy_id} 不存在")
        return strategy

    @staticmethod
    def update_strategy(
        db: Session,
        strategy_id: int,
        user_id: int,
        name: str | None = None,
        description: str | None = None,
        filter_conditions: list[dict[str, Any]] | None = None,
        selected_columns: list[str] | None = None,
        sort_config: list[dict[str, str]] | None = None,
        updated_by: str | None = None,
    ) -> StockFilterStrategy:
        """
        更新策略模板

        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            name: 策略名称
            description: 策略描述
            filter_conditions: 筛选条件
            selected_columns: 选中列
            sort_config: 排序配置
            updated_by: 修改人

        Returns:
            StockFilterStrategy: 更新后的策略记录

        Raises:
            NotFoundError: 策略不存在
        """
        strategy = StockFilterService.get_strategy_by_id(db, strategy_id, user_id)

        if name is not None:
            # 检查新名称是否与其他策略冲突
            existing = (
                db.query(StockFilterStrategy)
                .filter(
                    StockFilterStrategy.user_id == user_id,
                    StockFilterStrategy.name == name,
                    StockFilterStrategy.id != strategy_id,
                )
                .first()
            )
            if existing:
                raise ValidationError(f"策略名称 {name} 已存在")
            strategy.name = name

        if description is not None:
            strategy.description = description

        if filter_conditions is not None:
            strategy.filter_conditions = json.dumps(filter_conditions) if filter_conditions else None

        if selected_columns is not None:
            strategy.selected_columns = json.dumps(selected_columns) if selected_columns else None

        if sort_config is not None:
            strategy.sort_config = json.dumps(sort_config) if sort_config else None

        if updated_by is not None:
            strategy.updated_by = updated_by

        db.commit()
        db.refresh(strategy)

        return strategy

    @staticmethod
    def delete_strategy(db: Session, strategy_id: int, user_id: int) -> None:
        """
        删除策略模板

        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID

        Raises:
            NotFoundError: 策略不存在
        """
        strategy = StockFilterService.get_strategy_by_id(db, strategy_id, user_id)
        db.delete(strategy)
        db.commit()

    @staticmethod
    def get_strategy_stock_results(
        db: Session,
        trade_date: date,
        strategy_id: int,
        filter_conditions: list[dict[str, Any]] | None = None,
        sort_config: list[dict[str, str]] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取策略选股结果（直接查询反范式化字段，无需JOIN）

        Args:
            db: 数据库会话
            trade_date: 交易日期
            strategy_id: 策略ID
            filter_conditions: 筛选条件列表
            sort_config: 排序配置列表
            skip: 跳过记录数
            limit: 每页记录数

        Returns:
            (结果列表, 总数)
        """
        try:
            # 构建WHERE条件（使用结果表别名 r，不使用映射）
            where_clause, where_params = StockFilterService._build_filter_conditions(filter_conditions, use_mapping=False, table_alias="r")


            # 构建ORDER BY (使用结果表别名 r，不使用映射)
            order_by = StockFilterService._build_order_by(sort_config, table_alias="r", use_mapping=False)

            # 直接从结果表查询反范式化字段，无需JOIN
            from zquant.models.data import StockFilterResult
            select_columns = ", ".join([f"r.`{c.name}`" for c in StockFilterResult.__table__.columns if c.name != "id"])

            # 构建SQL查询 - 直接查询反范式化表，无需JOIN
            sql = f"""
            SELECT {select_columns}, COUNT(*) OVER() AS total_count
            FROM `zq_quant_stock_filter_result` r
            WHERE r.strategy_id = :strategy_id AND r.trade_date = :trade_date AND ({where_clause})
            {order_by}
            LIMIT :limit OFFSET :skip
            """

            # 合并参数
            params = {
                "strategy_id": strategy_id,
                "trade_date": trade_date,
                "skip": skip,
                "limit": limit,
                **where_params,
            }

            # 打印SQL日志
            log_sql_statement(sql, params)

            # 执行查询
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            columns = list(result.keys())

            items = []
            total = 0
            
            total_count_idx = None
            try:
                total_count_idx = columns.index("total_count")
            except ValueError:
                logger.warning("未找到total_count列")
            
            for row_idx, row in enumerate(rows):
                item = {}
                for col_idx, col in enumerate(columns):
                    if col_idx == total_count_idx:
                        if row_idx == 0:
                            value = row[col_idx]
                            total = int(value) if value is not None else 0
                        continue
                    
                    value = row[col_idx]
                    if hasattr(value, "isoformat"):
                        item[col] = value.isoformat()
                    elif isinstance(value, (int, float)) and value is not None:
                        item[col] = float(value)
                    else:
                        item[col] = value
                items.append(item)

            if len(rows) == 0:
                total = 0

            return items, total

        except Exception as e:
            logger.error(f"获取策略选股结果失败: {e}")
            raise ValidationError(f"获取策略选股结果失败: {str(e)}")

    @staticmethod
    def save_filter_results(
        db: Session,
        trade_date: date,
        strategy_id: int,
        strategy_name: str,
        stock_data: list[dict[str, Any]],
        username: str | None = None,
    ) -> int:
        """
        保存选股结果到数据库（包含反范式化数据）

        Args:
            db: 数据库会话
            trade_date: 交易日期
            strategy_id: 策略ID
            strategy_name: 策略名称
            stock_data: 股票数据列表，每个元素包含 ts_code 及其他反范式化字段
            username: 操作用户名

        Returns:
            保存的记录数
        """
        try:
            from zquant.models.data import StockFilterResult
            from sqlalchemy import insert, func
            from sqlalchemy.dialects.mysql import insert as mysql_insert

            if not stock_data:
                logger.info("没有需要保存的选股结果")
                return 0

            # 获取模型的所有列名（排除主键 id 和自动处理的时间戳列）
            # 我们需要保存反范式化字段，这些字段通常在 stock_data 中以相同的名称存在
            model_columns = [c.name for c in StockFilterResult.__table__.columns if c.name not in ["id", "created_time", "updated_time"]]
            
            # 准备批量插入数据，动态填充反范式化字段
            records = []
            for item in stock_data:
                ts_code = item.get("ts_code")
                if not ts_code:
                    continue
                    
                record = {
                    "trade_date": trade_date,
                    "ts_code": ts_code,
                    "strategy_id": strategy_id,
                    "strategy_name": strategy_name,
                    "created_by": username,
                    "updated_by": username,
                }
                
                # 动态填充其他反范式化字段
                for col in model_columns:
                    if col not in record and col in item:
                        record[col] = item.get(col)
                        
                records.append(record)

            if not records:
                logger.info("没有有效的选股结果可保存")
                return 0

            # 使用 MySQL ON DUPLICATE KEY UPDATE 语法同步所有字段
            stmt = mysql_insert(StockFilterResult).values(records)
            
            # 构建更新字段字典（排除唯一约束字段和创建相关字段）
            update_cols = {
                c: getattr(stmt.inserted, c)
                for c in model_columns 
                if c not in ["trade_date", "ts_code", "strategy_id", "created_by"]
            }
            # 确保更新时也更新 updated_by
            if username:
                update_cols["updated_by"] = username
            update_cols["updated_time"] = func.now()
            
            stmt = stmt.on_duplicate_key_update(**update_cols)

            result = db.execute(stmt)
            db.commit()

            saved_count = result.rowcount
            logger.info(f"保存选股结果成功: {saved_count} 条记录 (策略ID: {strategy_id}, 日期: {trade_date})")
            return saved_count

        except Exception as e:
            db.rollback()
            logger.error(f"保存选股结果失败: {e}")
            raise ValidationError(f"保存选股结果失败: {str(e)}")

