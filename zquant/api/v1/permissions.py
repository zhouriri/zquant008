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
权限管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from zquant.api.deps import get_current_active_user
from zquant.core.exceptions import NotFoundError, ValidationError
from zquant.core.permissions import check_permission
from zquant.database import get_db
from zquant.models.user import User
from zquant.schemas.common import QueryRequest
from zquant.schemas.user import (
    PageResponse,
    PermissionCreate,
    PermissionDeleteRequest,
    PermissionGetRequest,
    PermissionListRequest,
    PermissionResponse,
    PermissionUpdate,
)
from zquant.services.permission import PermissionService

router = APIRouter()


@router.post("", response_model=PageResponse, summary="查询权限列表")
@check_permission("permission", "read")
def get_permissions(
    request: PermissionListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询权限列表（分页、筛选、排序）"""
    permissions = PermissionService.get_all_permissions(
        db,
        skip=request.skip,
        limit=request.limit,
        resource=request.resource,
        order_by=request.order_by,
        order=request.order,
    )
    total = PermissionService.count_permissions(db, resource=request.resource)
    return PageResponse(
        items=[PermissionResponse.model_validate(p) for p in permissions],
        total=total,
        skip=request.skip,
        limit=request.limit,
    )


@router.post("/get", response_model=PermissionResponse, summary="查询权限详情")
@check_permission("permission", "read")
def get_permission(
    request: PermissionGetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """根据ID查询权限详情"""
    permission = PermissionService.get_permission_by_id(db, request.permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"权限ID {request.permission_id} 不存在")
    return permission


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED, summary="创建权限")
@check_permission("permission", "create")
def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建权限（需要permission:create权限）"""
    try:
        permission = PermissionService.create_permission(db, permission_data)
        return permission
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/update", response_model=PermissionResponse, summary="更新权限")
@check_permission("permission", "update")
def update_permission(
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新权限信息（需要permission:update权限）"""
    try:
        permission = PermissionService.update_permission(db, permission_data.id, permission_data)
        return permission
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/delete", summary="删除权限")
@check_permission("permission", "delete")
def delete_permission(
    request: PermissionDeleteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """删除权限（需要permission:delete权限）"""
    try:
        PermissionService.delete_permission(db, request.permission_id)
        return {"message": "权限已删除"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
