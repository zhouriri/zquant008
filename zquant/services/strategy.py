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

from typing import Optional
"""
策略服务
"""

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from loguru import logger

from zquant.models.backtest import Strategy


class StrategyService:
    """策略服务类"""

    @staticmethod
    def create_strategy(
        db: Session,
        user_id: int,
        name: str,
        code: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        params_schema: Optional[str] = None,
        is_template: bool = False,
        created_by: Optional[str] = None,
    ) -> Strategy:
        """创建策略"""
        strategy = Strategy(
            user_id=user_id,
            name=name,
            description=description,
            category=category,
            code=code,
            params_schema=params_schema,
            is_template=is_template,
            created_by=created_by,
            updated_by=created_by,  # 创建时 updated_by 和 created_by 一致
        )

        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        logger.info(f"创建策略: {strategy.id} - {strategy.name}")
        return strategy

    @staticmethod
    def get_strategy(db: Session, strategy_id: int, user_id: Optional[int] = None) -> Strategy | None:
        """
        获取策略详情

        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 当前用户ID（可选，如果提供则进行权限检查）

        Returns:
            策略对象或None
        """
        query = db.query(Strategy).filter(Strategy.id == strategy_id)
        strategy = query.first()

        if not strategy:
            return None

        # 如果提供了 user_id，则进行权限检查
        # 权限逻辑：用户自己的策略 OR 模板策略 对所有用户可见
        if user_id is not None:
            if strategy.user_id != user_id and not strategy.is_template:
                return None

        return strategy

    @staticmethod
    def update_strategy(
        db: Session,
        strategy_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        code: Optional[str] = None,
        params_schema: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> Strategy | None:
        """更新策略"""
        strategy = StrategyService.get_strategy(db, strategy_id, user_id)
        if not strategy:
            return None

        # 模板策略不允许普通用户修改
        if strategy.is_template and strategy.user_id != user_id:
            raise ValueError("模板策略不允许修改")

        if updated_by is not None:
            strategy.updated_by = updated_by

        if name is not None:
            strategy.name = name
        if description is not None:
            strategy.description = description
        if category is not None:
            strategy.category = category
        if code is not None:
            strategy.code = code
        if params_schema is not None:
            strategy.params_schema = params_schema

        db.commit()
        db.refresh(strategy)

        logger.info(f"更新策略: {strategy.id} - {strategy.name}")
        return strategy

    @staticmethod
    def delete_strategy(db: Session, strategy_id: int, user_id: int) -> bool:
        """删除策略"""
        strategy = StrategyService.get_strategy(db, strategy_id, user_id)
        if not strategy:
            return False

        # 模板策略不允许普通用户删除
        if strategy.is_template and strategy.user_id != user_id:
            raise ValueError("模板策略不允许删除")

        db.delete(strategy)
        db.commit()

        logger.info(f"删除策略: {strategy_id} - {strategy.name}")
        return True

    @staticmethod
    def list_strategies(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_template: Optional[bool] = None,
        order_by: Optional[str] = None,
        order: str = "desc",
    ) -> list[Strategy]:
        """获取策略列表（支持分类筛选、搜索、排序）"""
        query = db.query(Strategy).filter(Strategy.user_id == user_id)

        # 分类筛选
        if category:
            query = query.filter(Strategy.category == category)

        # 搜索（名称或描述）
        if search:
            query = query.filter((Strategy.name.contains(search)) | (Strategy.description.contains(search)))

        # 模板筛选
        if is_template is not None:
            query = query.filter(Strategy.is_template == is_template)

        # 排序逻辑
        if order_by:
            sortable_fields = {
                "id": Strategy.id,
                "name": Strategy.name,
                "category": Strategy.category,
                "created_time": Strategy.created_time,
                "updated_time": Strategy.updated_time,
            }

            if order_by in sortable_fields:
                sort_field = sortable_fields[order_by]
                if order and order.lower() == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(Strategy.created_time))
        else:
            query = query.order_by(desc(Strategy.created_time))

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_template_strategies(
        db: Session, category: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> list[Strategy]:
        """获取模板策略列表（所有用户可见）"""
        query = db.query(Strategy).filter(Strategy.is_template == True)

        # 分类筛选
        if category:
            query = query.filter(Strategy.category == category)

        return query.order_by(desc(Strategy.created_time)).offset(skip).limit(limit).all()

    @staticmethod
    def list_all_operable_strategies(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_template: Optional[bool] = None,
        order_by: Optional[str] = None,
        order: str = "desc",
    ) -> list[Strategy]:
        """
        获取所有可操作的策略列表
        包括：用户自己的策略、模板策略、其他用户的策略

        Args:
            db: 数据库会话
            user_id: 当前用户ID
            skip: 跳过记录数
            limit: 限制返回记录数
            category: 分类筛选
            search: 搜索关键词
            is_template: 是否模板筛选
            order_by: 排序字段
            order: 排序方向

        Returns:
            策略列表
        """
        from sqlalchemy import or_

        # 查询条件：用户自己的策略 OR 模板策略 OR 其他用户的策略（非模板）
        query = db.query(Strategy).filter(
            or_(
                Strategy.user_id == user_id,  # 用户自己的策略
                Strategy.is_template == True,  # 模板策略（所有用户可见）
                # 其他用户的策略（非模板）也可见，但不可编辑/删除
            )
        )

        # 分类筛选
        if category:
            query = query.filter(Strategy.category == category)

        # 搜索（名称或描述）
        if search:
            query = query.filter((Strategy.name.contains(search)) | (Strategy.description.contains(search)))

        # 模板筛选
        if is_template is not None:
            query = query.filter(Strategy.is_template == is_template)

        # 排序逻辑
        if order_by:
            sortable_fields = {
                "id": Strategy.id,
                "name": Strategy.name,
                "category": Strategy.category,
                "created_time": Strategy.created_time,
                "updated_time": Strategy.updated_time,
            }

            if order_by in sortable_fields:
                sort_field = sortable_fields[order_by]
                if order and order.lower() == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(Strategy.created_time))
        else:
            query = query.order_by(desc(Strategy.created_time))

        return query.offset(skip).limit(limit).all()
