# Copyright 2025 ZQuant Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Apache License is distributed on an "AS IS" BASIS,
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
超活跃组合因子计算器
包含换手率因子、小十字因子、半年统计因子
"""

from datetime import date, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from zquant.factor.calculators.base import BaseFactorCalculator
from zquant.models.data import get_daily_basic_table_name, get_daily_table_name
from zquant.services.data import DataService


class HyperActivityCalculator(BaseFactorCalculator):
    """超活跃组合因子计算器"""

    # 超活跃组合因子
    MODEL_CODE = "hyper_activity"

    def __init__(self, config: dict | None = None):
        """
        初始化超活跃组合因子计算器

        Args:
            config: 配置字典（当前未使用，保留用于未来扩展）
        """
        super().__init__(self.MODEL_CODE, config)

    def calculate(self, db: Session, code: str, trade_date: date) -> dict[str, Any] | None:
        """
        计算组合因子值（返回包含多个子因子的字典）

        Args:
            db: 数据库会话
            code: 股票代码（如：000001.SZ）
            trade_date: 交易日期

        Returns:
            包含所有子因子的字典，如果无法计算则返回None
        """
        try:
            result = {}

            # 1. 计算换手率因子（5/10/20/30/60/90日均值）
            turnover_factors = self._calculate_turnover_factors(db, code, trade_date)
            if turnover_factors is None:
                logger.warning(f"计算 {code} 换手率因子失败, date={trade_date}")
                return None
            result.update(turnover_factors)

            # 2. 计算小十字因子（振幅≤3%且涨跌幅≤1%的K线统计）
            xcross_factors = self._calculate_xcross_factors(db, code, trade_date)
            if xcross_factors is None:
                logger.warning(f"计算 {code} 小十字因子失败, date={trade_date}")
                return None
            result.update(xcross_factors)

            # 3. 计算半年统计因子
            halfyear_factors = self._calculate_halfyear_factors(db, code, trade_date)
            if halfyear_factors is None:
                logger.warning(f"计算 {code} 半年统计因子失败, date={trade_date}")
                return None
            result.update(halfyear_factors)

            return result

        except Exception as e:
            logger.error(f"计算超活跃组合因子失败: code={code}, trade_date={trade_date}, error={e}")
            return None

    def _calculate_turnover_factors(self, db: Session, code: str, trade_date: date) -> dict[str, Any] | None:
        """
        计算换手率因子

        Returns:
            包含换手率相关因子的字典
        """
        try:
            # 获取足够的历史数据（往前推90天，确保有足够交易日数据）
            start_date = trade_date - timedelta(days=90 * 2)
            daily_basic_data = DataService.get_daily_basic_data(
                db, ts_code=code, start_date=start_date, end_date=trade_date
            )

            if not daily_basic_data:
                logger.warning(f"未找到 {code} 在 {start_date} 到 {trade_date} 期间的每日指标数据")
                return None

            # 获取日线数据（用于获取成交额）
            daily_data = DataService.get_daily_data(db, ts_code=code, start_date=start_date, end_date=trade_date)

            # 将日线数据按日期索引
            daily_data_by_date = {}
            for record in daily_data:
                record_date = record.get("trade_date")
                if record_date is not None:
                    try:
                        if isinstance(record_date, str):
                            record_date = date.fromisoformat(record_date)
                        daily_data_by_date[record_date] = record
                    except (ValueError, TypeError):
                        continue

            # 过滤有效数据并按日期排序
            valid_records = []
            turnover_volume_records = []  # 用于统计换手率成交额累计条数
            for record in daily_basic_data:
                turnover_rate = record.get("turnover_rate")
                record_date = record.get("trade_date")
                if turnover_rate is not None and record_date is not None:
                    try:
                        if isinstance(record_date, str):
                            record_date = date.fromisoformat(record_date)
                        turnover_rate_value = float(turnover_rate)
                        valid_records.append((record_date, turnover_rate_value))

                        # 判断换手率成交额条件：换手率 >= 10% 且 成交额 >= 10亿
                        # amount 单位是千元，10亿 = 1,000,000 千元
                        daily_record = daily_data_by_date.get(record_date)
                        amount = daily_record.get("amount") if daily_record else None
                        
                        if (amount is not None and 
                            turnover_rate_value >= 10.0 and 
                            float(amount) * 1000 >= 1e9):
                            turnover_volume_records.append((record_date, 1.0))
                        else:
                            turnover_volume_records.append((record_date, 0.0))
                    except (ValueError, TypeError):
                        continue

            if not valid_records:
                logger.warning(f"{code} 在 {start_date} 到 {trade_date} 期间的换手率数据全部为空")
                return None

            # 按日期排序
            valid_records.sort(key=lambda x: x[0])
            turnover_volume_records.sort(key=lambda x: x[0])

            result = {}

            # 计算5/10/20/30/60/90日均值
            for days in [5, 10, 20, 30, 60, 90]:
                # 取最近days条记录
                recent_records = valid_records[-days:] if len(valid_records) >= days else valid_records
                if len(recent_records) >= days:
                    values = [value for _, value in recent_records]
                    ma_value = sum(values) / len(values)
                    result[f"ma{days}_tr"] = round(ma_value, 5)
                else:
                    result[f"ma{days}_tr"] = 0.0

            # 计算当日换手率成交额累计条数（满足换手率>=10%且成交额>=10亿则计数为1，否则为0）
            today_turnover_volume = next((r for r in turnover_volume_records if r[0] == trade_date), None)
            result["theday_turnover_volume"] = today_turnover_volume[1] if today_turnover_volume else 0.0

            # 计算5/10/20/30/60/90日换手率成交额累计条数（满足条件的条数）
            for days in [5, 10, 20, 30, 60, 90]:
                # 取最近days条记录
                recent_records = turnover_volume_records[-days:] if len(turnover_volume_records) >= days else turnover_volume_records
                # 统计满足条件的条数（值为1.0的记录数）
                count = sum(1 for _, value in recent_records if value == 1.0)
                result[f"total{days}_turnover_volume"] = float(count)

            return result

        except Exception as e:
            logger.error(f"计算换手率因子失败: code={code}, trade_date={trade_date}, error={e}")
            return None

    def _calculate_xcross_factors(self, db: Session, code: str, trade_date: date) -> dict[str, Any] | None:
        """
        计算小十字因子（振幅≤3%且涨跌幅≤1%的K线统计）

        Returns:
            包含小十字相关因子的字典
        """
        try:
            # 获取足够的历史数据（往前推90天）
            start_date = trade_date - timedelta(days=90 * 2)
            daily_data = DataService.get_daily_data(db, ts_code=code, start_date=start_date, end_date=trade_date)

            if not daily_data:
                logger.warning(f"未找到 {code} 在 {start_date} 到 {trade_date} 期间的日线数据")
                return None

            # 过滤有效数据并按日期排序
            valid_records = []
            for record in daily_data:
                high = record.get("high")
                low = record.get("low")
                pre_close = record.get("pre_close")
                pct_change = record.get("pct_chg")
                record_date = record.get("trade_date")

                if all(v is not None for v in [high, low, pre_close, pct_change, record_date]):
                    try:
                        if isinstance(record_date, str):
                            record_date = date.fromisoformat(record_date)
                        # 计算振幅 = (最高价 - 最低价) / 昨收价 * 100
                        amplitude = abs((float(high) - float(low)) / float(pre_close) * 100) if float(pre_close) > 0 else 0
                        # 涨跌幅的绝对值
                        pct_change_abs = abs(float(pct_change))
                        valid_records.append((record_date, amplitude, pct_change_abs))
                    except (ValueError, TypeError):
                        continue

            if not valid_records:
                logger.warning(f"{code} 在 {start_date} 到 {trade_date} 期间的日线数据全部无效")
                return None

            # 按日期排序
            valid_records.sort(key=lambda x: x[0])

            result = {}

            # 判断当日是否为小十字（振幅≤3%且涨跌幅≤1%）
            today_record = next((r for r in valid_records if r[0] == trade_date), None)
            if today_record:
                amplitude, pct_change_abs = today_record[1], today_record[2]
                result["theday_xcross"] = 1 if amplitude <= 3.0 and pct_change_abs <= 1.0 else 0
            else:
                result["theday_xcross"] = 0

            # 计算5/10/20/30/60/90日小十字累计条数
            for days in [5, 10, 20, 30, 60, 90]:
                recent_records = valid_records[-days:] if len(valid_records) >= days else valid_records
                xcross_count = sum(1 for r in recent_records if r[1] <= 3.0 and r[2] <= 1.0)
                result[f"total{days}_xcross"] = xcross_count

            return result

        except Exception as e:
            logger.error(f"计算小十字因子失败: code={code}, trade_date={trade_date}, error={e}")
            return None

    def _calculate_halfyear_factors(self, db: Session, code: str, trade_date: date) -> dict[str, Any] | None:
        """
        计算半年统计因子（半年内活跃次数、半年内换手率次数等）
        
        使用联合查询优化，直接在数据库层面过滤数据：
        - 成交额 > 10亿（amount > 100000 千元）
        - 换手率 >= 10%（turnover_rate >= 10）
        - 总市值或流通市值在50~200亿之间（total_mv 或 circ_mv 在 500000~2000000 万元之间）

        Returns:
            包含半年统计相关因子的字典
        """
        try:
            # 计算半年前的日期（约180天）
            halfyear_start = trade_date - timedelta(days=180)

            # 获取表名
            daily_table = get_daily_table_name(code)
            daily_basic_table = get_daily_basic_table_name(code)

            # 使用联合查询，直接在数据库层面过滤数据
            # 条件：
            # 1. 成交额 > 10亿（amount > 100000 千元）
            # 2. 换手率 >= 10%（turnover_rate >= 10）
            # 3. 总市值或流通市值在50~200亿之间（total_mv 或 circ_mv 在 500000~2000000 万元之间）
            sql = text(f"""
                SELECT COUNT(*) as count
                FROM `{daily_table}` d
                INNER JOIN `{daily_basic_table}` db
                    ON d.ts_code = db.ts_code 
                    AND d.trade_date = db.trade_date
                WHERE d.ts_code = :ts_code
                    AND d.trade_date >= :start_date
                    AND d.trade_date <= :end_date
                    AND d.amount > 100000
                    AND db.turnover_rate >= 10.0
                    AND (
                        (db.total_mv >= 500000 AND db.total_mv <= 2000000)
                        OR (db.circ_mv >= 500000 AND db.circ_mv <= 2000000)
                    )
            """)

            result = db.execute(
                sql,
                {
                    "ts_code": code,
                    "start_date": halfyear_start,
                    "end_date": trade_date,
                }
            )
            row = result.fetchone()

            if row is None:
                count = 0
            else:
                count = int(row[0]) if row[0] is not None else 0

            return {
                "halfyear_active_times": count,
                "halfyear_hsl_times": count,
            }

        except Exception as e:
            logger.error(f"计算半年统计因子失败: code={code}, trade_date={trade_date}, error={e}")
            # 如果查询失败（可能是表不存在），返回默认值
            return {
                "halfyear_active_times": 0,
                "halfyear_hsl_times": 0,
            }

    def validate_config(self) -> tuple[bool, str]:
        """
        验证配置是否有效

        Returns:
            (是否有效, 错误信息)
        """
        # 组合因子计算器当前不需要特殊配置
        return True, ""

    def get_required_data_tables(self) -> list[str]:
        """
        获取所需的数据表列表

        Returns:
            数据表名称列表
        """
        return [
            "zq_data_tustock_daily_*",  # 日线数据
            "zq_data_tustock_daily_basic_*",  # 每日指标数据
        ]


def main():
    """
    主函数：用于直接测试超活跃组合因子计算器
    
    用法:
        python -m zquant.factor.calculators.hyper_activity
        或
        python zquant/factor/calculators/hyper_activity.py
    """
    import sys as sys_module
    from pathlib import Path
    
    # 添加项目根目录到路径（确保能导入 zquant 模块）
    script_file = Path(__file__).resolve()
    # 找到项目根目录（包含 zquant 目录的目录）
    project_root = script_file.parent.parent.parent.parent
    if str(project_root) not in sys_module.path:
        sys_module.path.insert(0, str(project_root))
    
    from zquant.database import SessionLocal
    from loguru import logger
    
    # ==================== 参数配置（直接写死） ====================
    # 股票代码列表
    code_list = [
        "000001.SZ",
        "000002.SZ",
        # 可以在这里添加更多股票代码
        "301137.SZ",
    ]
    
    # 计算日期（None表示使用今天）
    trade_date = date.today()  # 或者指定日期: date(2025, 1, 10)
    
    # 是否显示详细输出
    verbose = True
    # ==================== 参数配置结束 ====================
    
    # 创建数据库会话
    db = SessionLocal()
    try:
        # 创建计算器
        calculator = HyperActivityCalculator()
        
        # 统计结果
        success_count = 0
        fail_count = 0
        results = []
        
        logger.info("=" * 80)
        logger.info(f"开始计算超活跃组合因子，日期: {trade_date}, 股票数量: {len(code_list)}")
        logger.info("=" * 80)
        
        # 遍历每个股票代码
        for idx, code in enumerate(code_list, 1):
            logger.info(f"\n[{idx}/{len(code_list)}] 计算股票: {code}")
            logger.info("-" * 80)
            
            try:
                # 计算因子
                result = calculator.calculate(db, code, trade_date)
                
                if result is None:
                    logger.warning(f"  ❌ {code} 计算失败：返回 None")
                    fail_count += 1
                    results.append({
                        "code": code,
                        "success": False,
                        "error": "返回 None",
                        "result": None,
                    })
                else:
                    logger.success(f"  ✅ {code} 计算成功")
                    success_count += 1
                    
                    # 显示关键指标
                    if verbose:
                        logger.info(f"  换手率因子:")
                        logger.info(f"    MA5:  {result.get('ma5_tr', 0):.4f}")
                        logger.info(f"    MA10: {result.get('ma10_tr', 0):.4f}")
                        logger.info(f"    MA20: {result.get('ma20_tr', 0):.4f}")
                        logger.info(f"    MA30: {result.get('ma30_tr', 0):.4f}")
                        logger.info(f"    MA60: {result.get('ma60_tr', 0):.4f}")
                        logger.info(f"    MA90: {result.get('ma90_tr', 0):.4f}")
                        logger.info(f"    当日换手率成交额累计条数: {result.get('theday_turnover_volume', 0)}")
                        logger.info(f"  小十字因子:")
                        logger.info(f"    当日小十字: {result.get('theday_xcross', 0)}")
                        logger.info(f"    5日累计: {result.get('total5_xcross', 0)}")
                        logger.info(f"    10日累计: {result.get('total10_xcross', 0)}")
                        logger.info(f"    20日累计: {result.get('total20_xcross', 0)}")
                        logger.info(f"    30日累计: {result.get('total30_xcross', 0)}")
                        logger.info(f"    60日累计: {result.get('total60_xcross', 0)}")
                        logger.info(f"    90日累计: {result.get('total90_xcross', 0)}")
                        logger.info(f"  半年统计因子:")
                        logger.info(f"    半年内活跃次数: {result.get('halfyear_active_times', 0)}")
                        logger.info(f"    半年内换手率次数: {result.get('halfyear_hsl_times', 0)}")
                    else:
                        # 简要输出
                        logger.info(f"  换手率MA5: {result.get('ma5_tr', 0):.4f}, "
                                  f"小十字当日: {result.get('theday_xcross', 0)}, "
                                  f"半年活跃: {result.get('halfyear_active_times', 0)}")
                    
                    results.append({
                        "code": code,
                        "success": True,
                        "result": result,
                    })
                    
            except Exception as e:
                logger.error(f"  ❌ {code} 计算异常: {str(e)}")
                if verbose:
                    import traceback
                    logger.error(traceback.format_exc())
                fail_count += 1
                results.append({
                    "code": code,
                    "success": False,
                    "error": str(e),
                    "result": None,
                })
        
        # 输出汇总
        logger.info("\n" + "=" * 80)
        logger.info("计算完成汇总")
        logger.info("=" * 80)
        logger.info(f"总股票数: {len(code_list)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {fail_count}")
        logger.info(f"成功率: {success_count / len(code_list) * 100:.2f}%")
        
        # 输出详细结果（JSON格式，便于后续处理）
        if verbose:
            import json
            logger.info("\n详细结果（JSON格式）:")
            logger.info(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        
        # 返回退出码
        return 0 if fail_count == 0 else 1
        
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    main()
