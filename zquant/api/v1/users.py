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
用户管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from zquant.api.deps import get_current_active_user
from zquant.core.exceptions import NotFoundError, ValidationError
from zquant.core.permissions import check_permission
from zquant.database import get_db
from zquant.models.user import User
from zquant.schemas.user import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyDeleteRequest,
    APIKeyResponse,
    PageResponse,
    PasswordReset,
    UserCreate,
    UserDeleteRequest,
    UserGetRequest,
    UserListRequest,
    UserResponse,
    UserUpdate,
)
from zquant.services.user import UserService

router = APIRouter()


@router.post("/query", response_model=PageResponse, summary="查询用户列表")
@check_permission("user", "read")
def get_users(
    request: UserListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询用户列表（分页、筛选、排序）"""
    users = UserService.get_all_users(
        db,
        skip=request.skip,
        limit=request.limit,
        is_active=request.is_active,
        role_id=request.role_id,
        username=request.username,
        order_by=request.order_by,
        order=request.order,
    )
    total = UserService.count_users(
        db, is_active=request.is_active, role_id=request.role_id, username=request.username
    )
    return PageResponse(
        items=[UserResponse.model_validate(u) for u in users], total=total, skip=request.skip, limit=request.limit
    )


@router.post("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户的信息"""
    try:
        logger.debug(f"[API] POST /api/v1/users/me - 用户ID: {current_user.id}, 用户名: {current_user.username}")
        logger.debug(
            f"[API] 用户信息详情: id={current_user.id}, username={current_user.username}, email={current_user.email}, role_id={current_user.role_id}, is_active={current_user.is_active}"
        )
        # FastAPI会自动使用response_model进行序列化
        result = current_user
        logger.debug(f"[API] 返回用户信息成功: user_id={current_user.id}")
        return result
    except Exception as e:
        # 记录详细错误信息以便调试
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户信息失败")


@router.post("/me/apikeys", response_model=list[APIKeyResponse], summary="获取API密钥列表")
def get_my_api_keys(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """获取当前用户的所有API密钥"""
    from zquant.services.apikey import APIKeyService

    api_keys = APIKeyService.get_user_api_keys(db, current_user.id)
    return api_keys


@router.post(
    "/me/apikeys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED, summary="创建API密钥"
)
def create_api_key(
    key_data: APIKeyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """创建API密钥"""
    from zquant.services.apikey import APIKeyService

    try:
        return APIKeyService.create_api_key(db, current_user.id, key_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/me/apikeys/delete", summary="删除API密钥")
def delete_api_key(request: APIKeyDeleteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """删除API密钥"""
    from zquant.core.exceptions import NotFoundError
    from zquant.services.apikey import APIKeyService

    try:
        APIKeyService.delete_api_key(db, request.key_id, current_user.id)
        return {"message": "API密钥已删除"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/get", response_model=UserResponse, summary="查询用户详情")
@check_permission("user", "read")
def get_user(request: UserGetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """根据ID查询用户详情"""
    user = UserService.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户ID {request.user_id} 不存在")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="创建用户")
@check_permission("user", "create")
def create_user(
    user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """创建用户（需要user:create权限）"""
    try:
        user = UserService.create_user(db, user_data, created_by=current_user.username)
        return user
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/update", response_model=UserResponse, summary="更新用户")
@check_permission("user", "update")
def update_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新用户信息（需要user:update权限）"""
    try:
        user = UserService.update_user(db, user_data.user_id, user_data, updated_by=current_user.username)
        return user
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password", summary="重置用户密码")
@check_permission("user", "update")
def reset_user_password(
    password_data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """重置用户密码（需要user:update权限）"""
    try:
        UserService.reset_password(db, password_data.user_id, password_data)
        return {"message": "密码重置成功"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/delete", summary="删除用户")
@check_permission("user", "delete")
def delete_user(request: UserDeleteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """删除用户（需要user:delete权限）"""
    try:
        UserService.delete_user(db, request.user_id)
        return {"message": "用户已删除"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
