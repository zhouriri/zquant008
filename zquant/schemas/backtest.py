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
回测相关Pydantic模型
"""

from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from zquant.schemas.common import QueryRequest


class BacktestConfig(BaseModel):
    """回测配置"""

    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    initial_capital: float = Field(1000000.0, description="初始资金")
    symbols: List[str] = Field(..., description="股票代码列表")
    frequency: str = Field("daily", description="频率：daily（日线）")
    adjust_type: str = Field("qfq", description="复权类型：qfq, hfq, None")
    commission_rate: float = Field(0.0003, description="佣金率")
    min_commission: float = Field(5.0, description="最低佣金")
    tax_rate: float = Field(0.001, description="印花税率")
    slippage_rate: float = Field(0.001, description="滑点率")
    benchmark: Optional[str] = Field(None, description="基准指数代码")
    use_daily_basic: bool = Field(False, description="是否使用每日指标数据")


class BacktestRunRequest(BaseModel):
    """运行回测请求"""

    strategy_id: Optional[int] = Field(None, description="策略ID（从策略库选择，可选）")
    strategy_code: Optional[str] = Field(None, description="策略代码（Python代码字符串，当strategy_id为空时必填）")
    strategy_name: str = Field(..., description="策略名称")
    config: BacktestConfig = Field(..., description="回测配置")


class BacktestTaskResponse(BaseModel):
    """回测任务响应"""

    id: int = Field(..., description="回测任务ID")
    user_id: int = Field(..., description="用户ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    status: str = Field(..., description="任务状态：pending, running, completed, failed")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_by: Optional[str] = Field(None, description="创建人")
    created_time: datetime = Field(..., description="创建时间")
    updated_by: Optional[str] = Field(None, description="修改人")
    updated_time: Optional[datetime] = Field(None, description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    start_date: Optional[date] = Field(None, description="回测数据开始日期（从配置中解析）")
    end_date: Optional[date] = Field(None, description="回测数据结束日期（从配置中解析）")

    class Config:
        from_attributes = True


class BacktestResultResponse(BaseModel):
    """回测结果响应"""

    id: int = Field(..., description="回测结果ID")
    task_id: int = Field(..., description="回测任务ID")
    total_return: Optional[float] = Field(None, description="总收益率")
    annual_return: Optional[float] = Field(None, description="年化收益率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    win_rate: Optional[float] = Field(None, description="胜率")
    profit_loss_ratio: Optional[float] = Field(None, description="盈亏比")
    alpha: Optional[float] = Field(None, description="Alpha（超额收益）")
    beta: Optional[float] = Field(None, description="Beta（市场敏感度）")
    metrics_json: Optional[str] = Field(None, description="绩效指标JSON（详细指标数据）")
    trades_json: Optional[str] = Field(None, description="交易记录JSON（所有交易记录）")
    portfolio_json: Optional[str] = Field(None, description="投资组合JSON（持仓变化数据）")
    created_by: Optional[str] = Field(None, description="创建人")
    created_time: datetime = Field(..., description="创建时间")
    updated_by: Optional[str] = Field(None, description="修改人")
    updated_time: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class PerformanceResponse(BaseModel):
    """绩效报告响应"""

    metrics: dict[str, Any] = Field(..., description="绩效指标")
    trades: List[dict[str, Any]] = Field(..., description="交易记录")
    portfolio: dict[str, Any] = Field(..., description="投资组合")


class StrategyCreateRequest(BaseModel):
    """创建策略请求"""

    name: str = Field(..., description="策略名称")
    code: str = Field(..., description="策略代码（Python代码字符串）")
    description: Optional[str] = Field(None, description="策略描述")
    category: Optional[str] = Field(None, description="策略分类：technical, fundamental, quantitative, etc.")
    params_schema: Optional[str] = Field(None, description="策略参数Schema（JSON格式）")
    is_template: bool = Field(False, description="是否为模板策略")


class StrategyUpdateRequest(BaseModel):
    """更新策略请求"""

    strategy_id: int = Field(..., description="策略ID")
    name: Optional[str] = Field(None, description="策略名称")
    code: Optional[str] = Field(None, description="策略代码（Python代码字符串）")
    description: Optional[str] = Field(None, description="策略描述")
    category: Optional[str] = Field(None, description="策略分类")
    params_schema: Optional[str] = Field(None, description="策略参数Schema（JSON格式）")


class StrategyDeleteRequest(BaseModel):
    """删除策略请求模型"""
    strategy_id: int = Field(..., description="策略ID")


class StrategyResponse(BaseModel):
    """策略响应"""

    id: int = Field(..., description="策略ID")
    user_id: int = Field(..., description="用户ID")
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    category: Optional[str] = Field(None, description="策略分类：technical, fundamental, quantitative等")
    code: str = Field(..., description="策略代码（Python代码字符串）")
    params_schema: Optional[str] = Field(None, description="策略参数Schema（JSON格式）")
    is_template: bool = Field(..., description="是否为模板策略")
    created_by: Optional[str] = Field(None, description="创建人")
    created_time: datetime = Field(..., description="创建时间")
    updated_by: Optional[str] = Field(None, description="修改人")
    updated_time: datetime = Field(..., description="更新时间")
    can_edit: Optional[bool] = Field(None, description="是否可以编辑")
    can_delete: Optional[bool] = Field(None, description="是否可以删除")

    class Config:
        from_attributes = True


class BacktestTaskListRequest(QueryRequest):
    """回测任务列表查询请求模型"""
    order_by: Optional[str] = Field(
        None, description="排序字段：id, name, status, created_time, updated_time"
    )


class BacktestTaskGetRequest(BaseModel):
    """获取回测任务请求模型"""
    task_id: int = Field(..., description="任务ID")


class BacktestResultGetRequest(BaseModel):
    """获取回测结果请求模型"""
    task_id: int = Field(..., description="任务ID")


class BacktestResultListRequest(QueryRequest):
    """回测结果列表查询请求模型"""
    order_by: Optional[str] = Field(
        None, description="排序字段：id, task_id, total_return, annual_return, created_time"
    )


class StrategyListRequest(QueryRequest):
    """策略列表查询请求模型"""
    category: Optional[str] = Field(None, description="策略分类筛选")
    search: Optional[str] = Field(None, description="搜索关键词（名称或描述）")
    is_template: Optional[bool] = Field(None, description="是否为模板策略")
    include_all: bool = Field(False, description="是否包含所有可操作策略（包括模板策略和其他用户的策略）")
    order_by: Optional[str] = Field(
        None, description="排序字段：id, name, category, created_time, updated_time"
    )


class StrategyGetRequest(BaseModel):
    """获取策略详情请求模型"""
    strategy_id: int = Field(..., description="策略ID")


class StrategyFrameworkResponse(BaseModel):
    """策略框架代码响应"""

    code: str = Field(..., description="策略框架代码")


class BacktestResultDeleteRequest(BaseModel):
    """删除回测结果请求模型"""
    result_id: int = Field(..., description="结果ID")
