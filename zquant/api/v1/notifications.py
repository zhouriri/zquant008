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
通知API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from zquant.api.deps import get_current_active_user
from zquant.core.exceptions import NotFoundError
from zquant.core.permissions import check_permission
from zquant.database import get_db
from zquant.models.notification import NotificationType
from zquant.models.user import User
from zquant.schemas.common import QueryRequest
from zquant.schemas.notification import (
    NotificationCreate,
    NotificationDeleteRequest,
    NotificationGetRequest,
    NotificationListRequest,
    NotificationListResponse,
    NotificationReadRequest,
    NotificationResponse,
    NotificationStatsResponse,
)
from zquant.services.notification import NotificationService

router = APIRouter()


@router.post("/query", response_model=NotificationListResponse, summary="获取通知列表")
def get_notifications(
    request: NotificationListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户通知列表（分页、筛选、排序）"""
    notifications, total = NotificationService.get_user_notifications(
        db,
        user_id=current_user.id,
        skip=request.skip,
        limit=request.limit,
        is_read=request.is_read,
        type=request.type,
        order_by=request.order_by,
        order=request.order,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        skip=request.skip,
        limit=request.limit,
    )


@router.post("/stats", response_model=NotificationStatsResponse, summary="获取未读统计")
def get_notification_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """获取通知统计（未读数量、总数量）"""
    unread_count = NotificationService.get_unread_count(db, current_user.id)
    total_count = NotificationService.get_total_count(db, current_user.id)
    return NotificationStatsResponse(unread_count=unread_count, total_count=total_count)


@router.post("/get", response_model=NotificationResponse, summary="获取通知详情")
def get_notification(
    request: NotificationGetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """获取通知详情"""
    try:
        notification = NotificationService.get_notification(db, request.notification_id, current_user.id)
        return NotificationResponse.model_validate(notification)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/read", response_model=NotificationResponse, summary="标记为已读")
def mark_notification_as_read(
    request: NotificationReadRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """标记单个通知为已读"""
    try:
        notification = NotificationService.mark_as_read(db, request.notification_id, current_user.id)
        return NotificationResponse.model_validate(notification)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/read-all", summary="全部标记为已读")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """标记所有通知为已读"""
    count = NotificationService.mark_all_as_read(db, current_user.id)
    return {"message": f"已标记 {count} 条通知为已读", "count": count}


@router.post("/delete", summary="删除通知")
def delete_notification(
    request: NotificationDeleteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """删除通知"""
    try:
        NotificationService.delete_notification(db, request.notification_id, current_user.id)
        return {"message": "通知已删除"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED, summary="创建通知")
@check_permission("notification", "create")
def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建通知（管理员或系统）"""
    notification = NotificationService.create_notification(db, notification_data, created_by=current_user.username)
    return NotificationResponse.model_validate(notification)
