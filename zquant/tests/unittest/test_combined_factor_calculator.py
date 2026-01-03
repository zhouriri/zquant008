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
组合因子计算器单元测试
"""

import unittest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from zquant.factor.calculators.combined import CombinedFactorCalculator

from .base import BaseTestCase


class TestCombinedFactorCalculator(BaseTestCase):
    """组合因子计算器测试"""

    def setUp(self):
        """每个测试方法执行前"""
        super().setUp()
        self.test_code = "000001.SZ"
        self.test_date = date(2025, 1, 10)
        self.calculator = CombinedFactorCalculator()

    # ==================== 换手率因子计算测试 ====================

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    def test_calculate_turnover_factors_success(self, mock_get_data):
        """测试成功计算换手率因子"""
        # 生成90天的测试数据
        test_data = []
        for i in range(90):
            trade_date = self.test_date - timedelta(days=90 - i)
            test_data.append({
                "trade_date": trade_date,
                "turnover_rate": 2.0 + (i % 10) * 0.1,  # 2.0 到 2.9 之间变化
            })

        mock_get_data.return_value = test_data

        # 执行计算
        result = self.calculator._calculate_turnover_factors(self.db, self.test_code, self.test_date)

        # 验证结果
        self.assertIsNotNone(result)
        # 检查是否包含所有预期的字段
        self.assertIn("ma5_tr", result)
        self.assertIn("ma10_tr", result)
        self.assertIn("ma20_tr", result)
        self.assertIn("ma30_tr", result)
        self.assertIn("ma60_tr", result)
        self.assertIn("ma90_tr", result)
        self.assertIn("theday_turnover_volume", result)
        self.assertIn("total5_turnover_volume", result)
        self.assertIn("total10_turnover_volume", result)
        self.assertIn("total20_turnover_volume", result)
        self.assertIn("total30_turnover_volume", result)
        self.assertIn("total60_turnover_volume", result)
        self.assertIn("total90_turnover_volume", result)

        # 验证均值计算（应该大于0）
        self.assertGreater(result["ma5_tr"], 0)
        self.assertGreater(result["ma10_tr"], 0)
        self.assertGreater(result["ma20_tr"], 0)
        self.assertGreater(result["ma30_tr"], 0)
        self.assertGreater(result["ma60_tr"], 0)
        self.assertGreater(result["ma90_tr"], 0)

        # 验证当日换手率成交额累计条数（应该有数据）
        self.assertEqual(result["theday_turnover_volume"], 1.0)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    def test_calculate_turnover_factors_no_data(self, mock_get_data):
        """测试没有数据时返回None"""
        mock_get_data.return_value = []

        result = self.calculator._calculate_turnover_factors(self.db, self.test_code, self.test_date)

        self.assertIsNone(result)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    def test_calculate_turnover_factors_insufficient_data(self, mock_get_data):
        """测试数据不足时返回默认值"""
        # 只提供5天的数据
        test_data = []
        for i in range(5):
            trade_date = self.test_date - timedelta(days=5 - i)
            test_data.append({
                "trade_date": trade_date,
                "turnover_rate": 2.0,
            })

        mock_get_data.return_value = test_data

        result = self.calculator._calculate_turnover_factors(self.db, self.test_code, self.test_date)

        # 应该返回结果，但某些长期均值为0
        self.assertIsNotNone(result)
        self.assertGreater(result["ma5_tr"], 0)
        self.assertEqual(result["ma90_tr"], 0.0)  # 数据不足，返回0

    # ==================== 小十字因子计算测试 ====================

    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_xcross_factors_success(self, mock_get_data):
        """测试成功计算小十字因子"""
        # 生成90天的测试数据
        test_data = []
        for i in range(90):
            trade_date = self.test_date - timedelta(days=90 - i)
            # 创建小十字K线（振幅≤3%且涨跌幅≤1%）
            pre_close = 10.0
            if i % 10 == 0:  # 每10天有一个小十字
                high = pre_close * 1.015  # 振幅1.5%
                low = pre_close * 0.985   # 振幅1.5%
                pct_change = 0.5  # 涨跌幅0.5%
            else:
                high = pre_close * 1.05  # 振幅5%
                low = pre_close * 0.95   # 振幅5%
                pct_change = 3.0  # 涨跌幅3%

            test_data.append({
                "trade_date": trade_date,
                "high": high,
                "low": low,
                "pre_close": pre_close,
                "pct_change": pct_change,
            })

        mock_get_data.return_value = test_data

        # 执行计算
        result = self.calculator._calculate_xcross_factors(self.db, self.test_code, self.test_date)

        # 验证结果
        self.assertIsNotNone(result)
        # 检查是否包含所有预期的字段
        self.assertIn("theday_xcross", result)
        self.assertIn("total5_xcross", result)
        self.assertIn("total10_xcross", result)
        self.assertIn("total20_xcross", result)
        self.assertIn("total30_xcross", result)
        self.assertIn("total60_xcross", result)
        self.assertIn("total90_xcross", result)

        # 验证小十字统计（应该有9个小十字，因为每10天一个，共90天）
        self.assertGreaterEqual(result["total90_xcross"], 8)
        self.assertLessEqual(result["total90_xcross"], 10)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_xcross_factors_no_data(self, mock_get_data):
        """测试没有数据时返回None"""
        mock_get_data.return_value = []

        result = self.calculator._calculate_xcross_factors(self.db, self.test_code, self.test_date)

        self.assertIsNone(result)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_xcross_factors_today_is_xcross(self, mock_get_data):
        """测试当日是小十字的情况"""
        # 当日是小十字
        test_data = [{
            "trade_date": self.test_date,
            "high": 10.15,  # 振幅1.5%
            "low": 9.85,    # 振幅1.5%
            "pre_close": 10.0,
            "pct_change": 0.5,  # 涨跌幅0.5%
        }]

        mock_get_data.return_value = test_data

        result = self.calculator._calculate_xcross_factors(self.db, self.test_code, self.test_date)

        self.assertIsNotNone(result)
        self.assertEqual(result["theday_xcross"], 1)  # 当日是小十字

    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_xcross_factors_today_is_not_xcross(self, mock_get_data):
        """测试当日不是小十字的情况"""
        # 当日不是小十字（振幅太大）
        test_data = [{
            "trade_date": self.test_date,
            "high": 10.5,   # 振幅5%
            "low": 9.5,     # 振幅5%
            "pre_close": 10.0,
            "pct_change": 2.0,  # 涨跌幅2%
        }]

        mock_get_data.return_value = test_data

        result = self.calculator._calculate_xcross_factors(self.db, self.test_code, self.test_date)

        self.assertIsNotNone(result)
        self.assertEqual(result["theday_xcross"], 0)  # 当日不是小十字

    # ==================== 半年统计因子计算测试 ====================

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_halfyear_factors_success(self, mock_get_daily, mock_get_basic):
        """测试成功计算半年统计因子"""
        # 生成180天的日线数据（半年）
        daily_data = []
        for i in range(180):
            trade_date = self.test_date - timedelta(days=180 - i)
            daily_data.append({
                "trade_date": trade_date,
                "vol": 1000000 if i % 2 == 0 else 0,  # 每隔一天有成交量
            })

        # 生成180天的每日指标数据
        basic_data = []
        for i in range(180):
            trade_date = self.test_date - timedelta(days=180 - i)
            basic_data.append({
                "trade_date": trade_date,
                "turnover_rate": 2.0 if i % 3 == 0 else None,  # 每3天有一个换手率数据
            })

        mock_get_daily.return_value = daily_data
        mock_get_basic.return_value = basic_data

        # 执行计算
        result = self.calculator._calculate_halfyear_factors(self.db, self.test_code, self.test_date)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn("halfyear_active_times", result)
        self.assertIn("halfyear_hsl_times", result)

        # 验证活跃次数（应该有90天有成交量）
        self.assertGreaterEqual(result["halfyear_active_times"], 80)
        self.assertLessEqual(result["halfyear_active_times"], 100)

        # 验证换手率次数（应该有约60个换手率数据）
        self.assertGreaterEqual(result["halfyear_hsl_times"], 50)
        self.assertLessEqual(result["halfyear_hsl_times"], 70)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_halfyear_factors_no_data(self, mock_get_daily, mock_get_basic):
        """测试没有数据时返回默认值"""
        mock_get_daily.return_value = []
        mock_get_basic.return_value = []

        result = self.calculator._calculate_halfyear_factors(self.db, self.test_code, self.test_date)

        # 应该返回默认值，而不是None
        self.assertIsNotNone(result)
        self.assertEqual(result["halfyear_active_times"], 0)
        self.assertEqual(result["halfyear_hsl_times"], 0)

    # ==================== 整体组合因子计算测试 ====================

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_combined_factor_success(self, mock_get_daily, mock_get_basic):
        """测试成功计算组合因子"""
        # 生成换手率数据
        basic_data = []
        for i in range(90):
            trade_date = self.test_date - timedelta(days=90 - i)
            basic_data.append({
                "trade_date": trade_date,
                "turnover_rate": 2.0,
            })

        # 生成日线数据
        daily_data = []
        for i in range(180):
            trade_date = self.test_date - timedelta(days=180 - i)
            daily_data.append({
                "trade_date": trade_date,
                "high": 10.15,
                "low": 9.85,
                "pre_close": 10.0,
                "pct_change": 0.5,
                "vol": 1000000,
            })

        # 设置mock返回值
        def get_daily_basic_data_side_effect(db, ts_code, start_date, end_date):
            # 根据日期范围返回不同的数据
            if end_date == self.test_date:
                return basic_data
            return basic_data

        def get_daily_data_side_effect(db, ts_code, start_date, end_date):
            return daily_data

        mock_get_basic.side_effect = get_daily_basic_data_side_effect
        mock_get_daily.side_effect = get_daily_data_side_effect

        # 执行计算
        result = self.calculator.calculate(self.db, self.test_code, self.test_date)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

        # 验证包含所有子因子
        # 换手率因子
        self.assertIn("ma5_tr", result)
        self.assertIn("ma10_tr", result)
        self.assertIn("theday_turnover_volume", result)
        # 小十字因子
        self.assertIn("theday_xcross", result)
        self.assertIn("total5_xcross", result)
        # 半年统计因子
        self.assertIn("halfyear_active_times", result)
        self.assertIn("halfyear_hsl_times", result)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    def test_calculate_combined_factor_turnover_fails(self, mock_get_basic):
        """测试换手率因子计算失败时返回None"""
        mock_get_basic.return_value = []  # 没有数据

        result = self.calculator.calculate(self.db, self.test_code, self.test_date)

        # 应该返回None，因为换手率因子计算失败
        self.assertIsNone(result)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_combined_factor_xcross_fails(self, mock_get_daily, mock_get_basic):
        """测试小十字因子计算失败时返回None"""
        # 换手率数据正常
        basic_data = [{
            "trade_date": self.test_date,
            "turnover_rate": 2.0,
        }]
        mock_get_basic.return_value = basic_data

        # 小十字数据为空
        mock_get_daily.return_value = []

        result = self.calculator.calculate(self.db, self.test_code, self.test_date)

        # 应该返回None，因为小十字因子计算失败
        self.assertIsNone(result)

    # ==================== 配置验证测试 ====================

    def test_validate_config(self):
        """测试配置验证"""
        is_valid, error_msg = self.calculator.validate_config()

        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")

    def test_get_required_data_tables(self):
        """测试获取所需数据表列表"""
        tables = self.calculator.get_required_data_tables()

        self.assertIsInstance(tables, list)
        self.assertIn("zq_data_tustock_daily_*", tables)
        self.assertIn("zq_data_tustock_daily_basic_*", tables)

    # ==================== 边界情况测试 ====================

    @patch("zquant.factor.calculators.combined.DataService.get_daily_basic_data")
    def test_calculate_turnover_factors_with_date_string(self, mock_get_data):
        """测试处理日期字符串格式的数据"""
        # 日期为字符串格式
        test_data = [{
            "trade_date": "2025-01-10",
            "turnover_rate": 2.5,
        }]

        mock_get_data.return_value = test_data

        result = self.calculator._calculate_turnover_factors(self.db, self.test_code, self.test_date)

        # 应该能正常处理
        self.assertIsNotNone(result)

    @patch("zquant.factor.calculators.combined.DataService.get_daily_data")
    def test_calculate_xcross_factors_edge_cases(self, mock_get_data):
        """测试小十字因子的边界情况"""
        # 测试振幅正好等于3%
        test_data = [{
            "trade_date": self.test_date,
            "high": 10.3,   # 振幅3%
            "low": 9.7,     # 振幅3%
            "pre_close": 10.0,
            "pct_change": 0.5,  # 涨跌幅0.5%
        }]

        mock_get_data.return_value = test_data

        result = self.calculator._calculate_xcross_factors(self.db, self.test_code, self.test_date)

        self.assertIsNotNone(result)
        # 振幅正好等于3%，应该算作小十字
        self.assertEqual(result["theday_xcross"], 1)

        # 测试涨跌幅正好等于1%
        test_data = [{
            "trade_date": self.test_date,
            "high": 10.15,  # 振幅1.5%
            "low": 9.85,    # 振幅1.5%
            "pre_close": 10.0,
            "pct_change": 1.0,  # 涨跌幅1%
        }]

        mock_get_data.return_value = test_data

        result = self.calculator._calculate_xcross_factors(self.db, self.test_code, self.test_date)

        self.assertIsNotNone(result)
        # 涨跌幅正好等于1%，应该算作小十字
        self.assertEqual(result["theday_xcross"], 1)


if __name__ == "__main__":
    unittest.main()
