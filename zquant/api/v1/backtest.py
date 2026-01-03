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
回测API
"""

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from zquant.api.deps import get_current_active_user
from zquant.database import get_db
from zquant.models.user import User
from zquant.schemas.backtest import (
    BacktestResultDeleteRequest,
    BacktestResultGetRequest,
    BacktestResultListRequest,
    BacktestResultResponse,
    BacktestRunRequest,
    BacktestTaskGetRequest,
    BacktestTaskListRequest,
    BacktestTaskResponse,
    PerformanceResponse,
    StrategyCreateRequest,
    StrategyDeleteRequest,
    StrategyFrameworkResponse,
    StrategyGetRequest,
    StrategyListRequest,
    StrategyResponse,
    StrategyUpdateRequest,
)
from zquant.services.backtest import BacktestService
from zquant.services.strategy import StrategyService

router = APIRouter()


def _build_task_response(task) -> BacktestTaskResponse:
    """构建回测任务响应，从 config_json 中解析 start_date 和 end_date"""
    start_date = None
    end_date = None

    if task.config_json:
        try:
            config = json.loads(task.config_json)
            if "start_date" in config:
                start_date = (
                    date.fromisoformat(config["start_date"])
                    if isinstance(config["start_date"], str)
                    else config["start_date"]
                )
            if "end_date" in config:
                end_date = (
                    date.fromisoformat(config["end_date"])
                    if isinstance(config["end_date"], str)
                    else config["end_date"]
                )
        except (json.JSONDecodeError, ValueError, TypeError):
            # 如果解析失败，保持为 None
            pass

    return BacktestTaskResponse(
        id=task.id,
        user_id=task.user_id,
        strategy_name=task.strategy_name,
        status=task.status.value,
        error_message=task.error_message,
        created_time=task.created_time,
        started_at=task.started_at,
        completed_at=task.completed_at,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/run", response_model=BacktestTaskResponse, status_code=status.HTTP_201_CREATED, summary="运行回测")
def run_backtest(
    request: BacktestRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """运行回测任务"""
    try:
        # 创建任务（支持从策略库选择或直接提供策略代码）
        task = BacktestService.create_task(
            db,
            current_user.id,
            request.strategy_name,
            request.config.dict(),
            strategy_id=request.strategy_id,
            strategy_code=request.strategy_code,
            created_by=current_user.username,
        )

        # 异步运行回测（这里简化处理，直接同步运行）
        # 生产环境应使用Celery异步任务
        try:
            BacktestService.run_backtest(db, task.id, updated_by=current_user.username)
        except Exception:
            # 错误已在任务中记录
            pass

        # 重新加载任务以获取最新状态
        db.refresh(task)
        return _build_task_response(task)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建回测任务失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建回测任务失败")


@router.post("/tasks", response_model=list[BacktestTaskResponse], summary="获取回测任务列表")
def get_backtest_tasks(
    request: BacktestTaskListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户的所有回测任务列表"""
    tasks = BacktestService.get_user_tasks(
        db, current_user.id, request.skip, request.limit, order_by=request.order_by, order=request.order
    )
    return [_build_task_response(task) for task in tasks]


@router.post("/tasks/get", response_model=BacktestTaskResponse, summary="获取回测任务详情")
def get_backtest_task(
    request: BacktestTaskGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取单个回测任务详情"""
    task = BacktestService.get_task(db, request.task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回测任务不存在")
    return _build_task_response(task)


@router.post("/tasks/result", response_model=BacktestResultResponse, summary="获取回测结果详情")
def get_backtest_result(
    request: BacktestResultGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取回测结果详情（仅基本信息）"""
    result = BacktestService.get_result(db, request.task_id, current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回测结果不存在")
    return result




@router.post("/tasks/performance", response_model=PerformanceResponse, summary="获取绩效报告")
def get_performance(
    request: BacktestResultGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取绩效报告（包含详细指标、交易记录、投资组合）"""
    result = BacktestService.get_result(db, request.task_id, current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回测结果不存在")

    import json

    return PerformanceResponse(
        metrics=json.loads(result.metrics_json) if result.metrics_json else {},
        trades=json.loads(result.trades_json) if result.trades_json else [],
        portfolio=json.loads(result.portfolio_json) if result.portfolio_json else {},
    )


# ========== 策略管理API ==========


@router.post("/strategies/framework", response_model=StrategyFrameworkResponse, summary="获取策略框架代码")
def get_strategy_framework():
    """获取策略框架代码模板"""
    framework_code = """from zquant.backtest.context import Context
from zquant.backtest.strategy import BaseStrategy

class Strategy(BaseStrategy):
    def initialize(self):
        \"\"\"策略初始化，设置参数等\"\"\"
        # 在这里设置策略参数
        # 例如：self.max_pe = self.params.get("max_pe", 30.0)
        pass
    
    def on_bar(self, context: Context, bar_data: dict):
        \"\"\"K线数据回调
        
        Args:
            context: 回测上下文，包含：
                - context.portfolio: 投资组合（持仓、现金、总资产）
                - context.current_date: 当前日期
                - context.order(symbol, quantity, price): 下单函数
                - context.order_target(symbol, target_quantity): 目标持仓下单
                - context.order_value(symbol, value): 按金额下单
                - context.order_target_value(symbol, target_value): 目标市值下单
                - context.get_daily_basic(symbol): 获取每日指标数据（需启用use_daily_basic）
            bar_data: K线数据，格式：{symbol: {open, high, low, close, volume, ...}}
        \"\"\"
        for symbol, bar in bar_data.items():
            # 获取当前价格
            current_price = bar["close"]
            
            # 获取持仓
            pos = context.portfolio.get_position(symbol)
            
            # 获取每日指标数据（如果启用了use_daily_basic）
            # daily_basic = context.get_daily_basic(symbol)
            # if daily_basic:
            #     pe = daily_basic.get("pe")  # 市盈率
            #     pb = daily_basic.get("pb")  # 市净率
            #     turnover_rate = daily_basic.get("turnover_rate")  # 换手率
            
            # 在这里编写您的交易逻辑
            # 示例：买入
            # if 某个条件:
            #     context.order_target_value(symbol, 100000)  # 买入10万元
            
            # 示例：卖出
            # if 某个条件 and pos.quantity > 0:
            #     context.order_target(symbol, 0)  # 清仓
"""
    return StrategyFrameworkResponse(code=framework_code)


@router.post("/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED, summary="创建策略")
def create_strategy(
    request: StrategyCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """创建策略"""
    try:
        strategy = StrategyService.create_strategy(
            db,
            current_user.id,
            request.name,
            request.code,
            request.description,
            request.category,
            request.params_schema,
            request.is_template,
            created_by=current_user.username,
        )
        return strategy
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建策略失败")


@router.post("/strategies/list", response_model=list[StrategyResponse], summary="获取策略列表")
def get_strategies(
    request: StrategyListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取策略列表

    - 如果 include_all=False：仅返回当前用户的策略
    - 如果 include_all=True：返回所有可操作策略（用户自己的策略 + 模板策略 + 其他用户的策略）
    """
    if request.include_all:
        strategies = StrategyService.list_all_operable_strategies(
            db,
            current_user.id,
            request.skip,
            request.limit,
            category=request.category,
            search=request.search,
            is_template=request.is_template,
            order_by=request.order_by,
            order=request.order,
        )
    else:
        strategies = StrategyService.list_strategies(
            db,
            current_user.id,
            request.skip,
            request.limit,
            category=request.category,
            search=request.search,
            is_template=request.is_template,
            order_by=request.order_by,
            order=request.order,
        )

    # 添加权限字段
    result = []
    for strategy in strategies:
        # 判断是否可以编辑
        can_edit = strategy.user_id == current_user.id
        # 如果是模板策略且不是创建者，不能编辑
        if strategy.is_template and strategy.user_id != current_user.id:
            can_edit = False

        # 判断是否可以删除
        can_delete = strategy.user_id == current_user.id
        # 如果是模板策略且不是创建者，不能删除
        if strategy.is_template and strategy.user_id != current_user.id:
            can_delete = False

        strategy_dict = {
            "id": strategy.id,
            "user_id": strategy.user_id,
            "name": strategy.name,
            "description": strategy.description,
            "category": strategy.category,
            "code": strategy.code,
            "params_schema": strategy.params_schema,
            "is_template": strategy.is_template,
            "created_time": strategy.created_time,
            "updated_time": strategy.updated_time,
            "can_edit": can_edit,
            "can_delete": can_delete,
        }
        result.append(StrategyResponse(**strategy_dict))

    return result


@router.post("/strategies/get", response_model=StrategyResponse, summary="获取策略详情")
def get_strategy(
    request: StrategyGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取单个策略详情"""
    strategy = StrategyService.get_strategy(db, request.strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="策略不存在")
    
    # 判断是否可以编辑
    can_edit = strategy.user_id == current_user.id
    if strategy.is_template and strategy.user_id != current_user.id:
        can_edit = False

    # 判断是否可以删除
    can_delete = strategy.user_id == current_user.id
    if strategy.is_template and strategy.user_id != current_user.id:
        can_delete = False

    strategy_dict = {
        "id": strategy.id,
        "user_id": strategy.user_id,
        "name": strategy.name,
        "description": strategy.description,
        "category": strategy.category,
        "code": strategy.code,
        "params_schema": strategy.params_schema,
        "is_template": strategy.is_template,
        "created_time": strategy.created_time,
        "updated_time": strategy.updated_time,
        "can_edit": can_edit,
        "can_delete": can_delete,
    }
    return StrategyResponse(**strategy_dict)


@router.post("/strategies/templates", response_model=list[StrategyResponse], summary="获取模板策略列表")
def get_template_strategies(
    request: StrategyListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取模板策略列表（所有用户可见）"""
    strategies = StrategyService.get_template_strategies(
        db, category=request.category, skip=request.skip, limit=request.limit
    )
    return strategies


@router.post("/strategies/update", response_model=StrategyResponse, summary="更新策略")
def update_strategy(
    request: StrategyUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新策略"""
    try:
        strategy = StrategyService.update_strategy(
            db,
            request.strategy_id,
            current_user.id,
            name=request.name,
            description=request.description,
            category=request.category,
            code=request.code,
            params_schema=request.params_schema,
            updated_by=current_user.username,
        )
        if not strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"策略 {request.strategy_id} 不存在")
        return strategy
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新策略失败")


@router.post("/strategies/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除策略")
def delete_strategy(
    request: StrategyDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除策略"""
    try:
        success = StrategyService.delete_strategy(db, request.strategy_id, current_user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"策略 {request.strategy_id} 不存在")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除策略失败")


# ========== 回测结果管理API ==========


@router.post("/results", response_model=list[BacktestResultResponse], summary="获取回测结果列表")
def get_backtest_results(
    request: BacktestResultListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户的所有回测结果列表（支持排序）"""
    results = BacktestService.list_results(
        db, current_user.id, request.skip, request.limit, order_by=request.order_by, order=request.order
    )
    return results


@router.post("/results/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除回测结果")
def delete_backtest_result(
    request: BacktestResultDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除回测结果（级联删除任务）"""
    success = BacktestService.delete_result(db, request.result_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"回测结果 {request.result_id} 不存在")
