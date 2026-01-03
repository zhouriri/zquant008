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
因子管理API
"""

from datetime import date, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from loguru import logger
from sqlalchemy.orm import Session

from zquant.api.deps import get_current_active_user
from zquant.core.exceptions import NotFoundError, ValidationError
from zquant.core.permissions import is_admin
from zquant.database import get_db
from zquant.models.user import User
from zquant.schemas.factor import (
    FactorCalculationRequest,
    FactorCalculationResponse,
    FactorConfigCreate,
    FactorConfigDeleteRequest,
    FactorConfigGetRequest,
    FactorConfigGroupedListRequest,
    FactorConfigGroupedListResponse,
    FactorConfigGroupedResponse,
    FactorConfigListRequest,
    FactorConfigListResponse,
    FactorConfigResponse,
    FactorConfigSingleDeleteRequest,
    FactorConfigSingleUpdate,
    FactorConfigUpdate,
    FactorDefinitionCreate,
    FactorDefinitionDeleteRequest,
    FactorDefinitionGetRequest,
    FactorDefinitionListRequest,
    FactorDefinitionListResponse,
    FactorDefinitionResponse,
    FactorDefinitionUpdate,
    FactorModelCreate,
    FactorModelDeleteRequest,
    FactorModelGetRequest,
    FactorModelListRequest,
    FactorModelListResponse,
    FactorModelResponse,
    FactorModelUpdate,
    FactorResultItem,
    FactorResultQueryRequest,
    FactorResultResponse,
    QuantFactorQueryRequest,
    QuantFactorQueryResponse,
)
from zquant.services.factor import FactorService
from zquant.services.factor_calculation import FactorCalculationService

router = APIRouter()


# ==================== 因子定义管理 ====================

@router.post("/definitions", response_model=FactorDefinitionResponse, status_code=status.HTTP_201_CREATED, summary="创建因子定义")
def create_factor_definition(
    factor_data: FactorDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建因子定义（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        factor_def = FactorService.create_factor_definition(
            db=db,
            factor_name=factor_data.factor_name,
            cn_name=factor_data.cn_name,
            en_name=factor_data.en_name,
            column_name=factor_data.column_name,
            description=factor_data.description,
            factor_type=factor_data.factor_type,
            enabled=factor_data.enabled,
            factor_config=factor_data.factor_config,
            created_by=current_user.username,
        )
        return FactorDefinitionResponse.from_orm(factor_def)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建因子定义失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建因子定义失败")


@router.post("/definitions/query", response_model=FactorDefinitionListResponse, summary="获取因子定义列表")
def list_factor_definitions(
    request: FactorDefinitionListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子定义列表"""
    try:
        items, total = FactorService.list_factor_definitions(
            db=db,
            skip=request.skip,
            limit=request.limit,
            enabled=request.enabled,
            order_by=request.order_by,
            order=request.order,
        )
        return FactorDefinitionListResponse(
            items=[FactorDefinitionResponse.from_orm(item) for item in items], total=total
        )
    except Exception as e:
        logger.error(f"获取因子定义列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子定义列表失败")


@router.post("/definitions/get", response_model=FactorDefinitionResponse, summary="获取因子定义")
def get_factor_definition(
    request: FactorDefinitionGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子定义"""
    try:
        factor_def = FactorService.get_factor_definition(db, request.factor_id)
        return FactorDefinitionResponse.from_orm(factor_def)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取因子定义失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子定义失败")


@router.post("/definitions/update", response_model=FactorDefinitionResponse, summary="更新因子定义")
def update_factor_definition(
    factor_data: FactorDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新因子定义（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        factor_def = FactorService.update_factor_definition(
            db=db,
            factor_id=factor_data.factor_id,
            cn_name=factor_data.cn_name,
            en_name=factor_data.en_name,
            column_name=factor_data.column_name,
            description=factor_data.description,
            factor_type=factor_data.factor_type,
            enabled=factor_data.enabled,
            factor_config=factor_data.factor_config,
            updated_by=current_user.username,
        )
        return FactorDefinitionResponse.from_orm(factor_def)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新因子定义失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新因子定义失败")


@router.post("/definitions/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除因子定义")
def delete_factor_definition(
    request: FactorDefinitionDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除因子定义（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        FactorService.delete_factor_definition(db, request.factor_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除因子定义失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除因子定义失败")


# ==================== 因子模型管理 ====================

@router.post("/models", response_model=FactorModelResponse, status_code=status.HTTP_201_CREATED, summary="创建因子模型")
def create_factor_model(
    model_data: FactorModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建因子模型（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        model = FactorService.create_factor_model(
            db=db,
            factor_id=model_data.factor_id,
            model_name=model_data.model_name,
            model_code=model_data.model_code,
            config_json=model_data.config_json,
            is_default=model_data.is_default,
            enabled=model_data.enabled,
            created_by=current_user.username,
        )
        return FactorModelResponse.from_orm(model)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建因子模型失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建因子模型失败")


@router.post("/models/query", response_model=FactorModelListResponse, summary="获取因子模型列表")
def list_factor_models(
    request: FactorModelListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子模型列表"""
    try:
        items, total = FactorService.list_factor_models(
            db=db,
            factor_id=request.factor_id,
            skip=request.skip,
            limit=request.limit,
            enabled=request.enabled,
            order_by=request.order_by,
            order=request.order,
        )
        return FactorModelListResponse(items=[FactorModelResponse.from_orm(item) for item in items], total=total)
    except Exception as e:
        logger.error(f"获取因子模型列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子模型列表失败")


@router.post("/models/get", response_model=FactorModelResponse, summary="获取因子模型")
def get_factor_model(
    request: FactorModelGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子模型"""
    try:
        model = FactorService.get_factor_model(db, request.model_id)
        return FactorModelResponse.from_orm(model)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取因子模型失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子模型失败")


@router.post("/models/update", response_model=FactorModelResponse, summary="更新因子模型")
def update_factor_model(
    model_data: FactorModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新因子模型（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        model = FactorService.update_factor_model(
            db=db,
            model_id=model_data.model_id,
            model_name=model_data.model_name,
            model_code=model_data.model_code,
            config_json=model_data.config_json,
            is_default=model_data.is_default,
            enabled=model_data.enabled,
            updated_by=current_user.username,
        )
        return FactorModelResponse.from_orm(model)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新因子模型失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新因子模型失败")


@router.post("/models/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除因子模型")
def delete_factor_model(
    request: FactorModelDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除因子模型（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        FactorService.delete_factor_model(db, request.model_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除因子模型失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除因子模型失败")


# ==================== 因子配置管理（新表结构，标准RESTful接口） ====================

@router.post("/configs", response_model=FactorConfigResponse, status_code=status.HTTP_201_CREATED, summary="创建因子配置")
def create_factor_config(
    config_data: FactorConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建因子配置（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        config = FactorService.create_factor_config(
            db=db,
            factor_id=config_data.factor_id,
            config=config_data.to_config_dict(),
            created_by=current_user.username,
        )
        return FactorConfigResponse.from_orm(config)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建因子配置失败")


@router.post("/configs/query", response_model=FactorConfigListResponse, summary="获取因子配置列表")
def list_factor_configs(
    request: FactorConfigListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子配置列表"""
    try:
        items, total = FactorService.list_factor_configs(
            db=db,
            skip=request.skip,
            limit=request.limit,
            enabled=request.enabled,
            order_by=request.order_by,
            order=request.order,
        )
        return FactorConfigListResponse(
            items=[FactorConfigResponse.from_orm(item) for item in items], total=total
        )
    except Exception as e:
        logger.error(f"获取因子配置列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子配置列表失败")


@router.post("/configs/get", response_model=FactorConfigResponse, summary="获取因子配置")
def get_factor_config_by_id(
    request: FactorConfigGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子配置"""
    try:
        config = FactorService.get_factor_config_by_factor_id(db, request.factor_id)
        return FactorConfigResponse.from_orm(config)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子配置失败")


@router.post("/configs/update", response_model=FactorConfigResponse, summary="更新因子配置")
def update_factor_config_by_id(
    config_data: FactorConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新因子配置（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 获取当前配置
        current_config_obj = FactorService.get_factor_config_by_factor_id(db, config_data.factor_id)
        current_config = current_config_obj.get_config()
        
        # 使用传入的映射和状态构建新配置
        new_config = current_config.copy()
        if config_data.mappings is not None:
            new_config["mappings"] = [{"model_id": m.model_id, "codes": m.codes} for m in config_data.mappings]
        if config_data.enabled is not None:
            new_config["enabled"] = config_data.enabled
        
        config = FactorService.update_factor_config_by_factor_id(
            db=db,
            factor_id=config_data.factor_id,
            config=new_config,
            updated_by=current_user.username,
        )
        return FactorConfigResponse.from_orm(config)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"更新因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新因子配置失败")


@router.post("/configs/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除因子配置")
def delete_factor_config_by_id(
    request: FactorConfigDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除因子配置（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        FactorService.delete_factor_config_by_factor_id(db, request.factor_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除因子配置失败")


# ==================== 因子配置管理（基于JSON，已废弃，向后兼容） ====================

@router.post("/definitions/config", response_model=dict, summary="获取因子配置（已废弃）")
def get_factor_config(
    request: FactorConfigGetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取因子配置（已废弃）
    
    注意：此接口已废弃，请使用 POST /api/v1/factor/configs/get 代替
    """
    try:
        # 尝试从新表获取
        try:
            config_obj = FactorService.get_factor_config_by_factor_id(db, request.factor_id)
            return config_obj.get_config()
        except NotFoundError:
            # 如果新表不存在，从旧表获取（向后兼容）
            config = FactorService.get_factor_config(db, request.factor_id)
            return config
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子配置失败")


@router.post("/definitions/config/update", response_model=dict, summary="更新因子配置（已废弃）")
def update_factor_config(
    factor_id: int = Body(..., description="因子ID"),
    factor_config: dict = Body(..., description="配置内容"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新因子配置（已废弃）
    
    注意：此接口已废弃，请使用 POST /api/v1/factor/configs/update 代替
    """
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 尝试更新新表
        try:
            config_obj = FactorService.get_factor_config_by_factor_id(db, factor_id)
            config_obj = FactorService.update_factor_config_by_factor_id(
                db, factor_id, factor_config, updated_by=current_user.username
            )
            return config_obj.get_config()
        except NotFoundError:
            # 如果新表不存在，更新旧表（向后兼容）
            factor_def = FactorService.update_factor_config(db, factor_id, factor_config)
            return factor_def.get_factor_config()
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"更新因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新因子配置失败")


@router.post("/definitions/config/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除因子配置（已废弃）")
def delete_factor_config(
    request: FactorConfigDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除因子配置（已废弃）
    
    注意：此接口已废弃，请使用 POST /api/v1/factor/configs/delete 代替
    """
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 尝试删除新表
        try:
            FactorService.delete_factor_config_by_factor_id(db, request.factor_id)
        except NotFoundError:
            # 如果新表不存在，清空旧表配置（向后兼容）
            factor_def = FactorService.get_factor_definition(db, request.factor_id)
            factor_def.set_factor_config({})
            db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除因子配置失败")


# ==================== 因子配置管理（已废弃，仅用于向后兼容） ====================

@router.post("/configs", response_model=FactorConfigGroupedResponse, status_code=status.HTTP_201_CREATED, summary="创建因子配置（支持多映射）（已废弃）")
def create_factor_config(
    config_data: FactorConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建因子配置（支持多映射）（已废弃）
    
    注意：此接口已废弃，请使用 PUT /definitions/{factor_id}/config 代替
    """
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 转换映射数据格式为JSON配置格式
        factor_config = {
            "enabled": config_data.enabled,
            "mappings": [{"model_id": m.model_id, "codes": m.codes} for m in config_data.mappings]
        }
        
        # 使用新的update_factor_config方法
        factor_def = FactorService.update_factor_config(
            db=db,
            factor_id=config_data.factor_id,
            factor_config=factor_config,
        )
        
        config = factor_def.get_factor_config()
        mappings = [FactorConfigResponse(
            id=0,  # 占位符，实际不存在
            factor_id=config_data.factor_id,
            model_id=m.get("model_id"),
            codes=m.get("codes"),
            enabled=config.get("enabled", True),
            created_time=factor_def.created_time,
            updated_time=factor_def.updated_time,
        ) for m in config.get("mappings", [])]
        
        return FactorConfigGroupedResponse(
            factor_id=config_data.factor_id,
            enabled=config.get("enabled", True),
            mappings=mappings,
            created_time=factor_def.created_time,
            updated_time=factor_def.updated_time,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建因子配置失败")


@router.post("/configs/grouped", response_model=FactorConfigGroupedListResponse, summary="获取因子配置列表（按因子分组）")
def list_factor_configs_grouped(
    request: FactorConfigGroupedListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子配置列表（按因子ID分组，每个因子包含所有映射）"""
    try:
        # 获取所有配置
        all_configs, _ = FactorService.list_factor_configs(db=db, enabled=request.enabled, limit=10000)
        
        # 按factor_id分组
        grouped: dict[int, list] = {}
        for config in all_configs:
            if config.factor_id not in grouped:
                grouped[config.factor_id] = []
            grouped[config.factor_id].append(config)
        
        # 构建响应
        items = []
        for factor_id, configs in grouped.items():
            if configs:
                items.append(FactorConfigGroupedResponse(
                    factor_id=factor_id,
                    enabled=configs[0].enabled,
                    mappings=[FactorConfigResponse.from_orm(c) for c in configs],
                    created_time=min(c.created_time for c in configs),
                    updated_time=max(c.updated_time for c in configs),
                ))
        
        return FactorConfigGroupedListResponse(items=items, total=len(items))
    except Exception as e:
        logger.error(f"获取因子配置列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子配置列表失败")


@router.post("/configs/by-factor/update", response_model=FactorConfigGroupedResponse, summary="更新因子配置（按因子ID，支持多映射）（已废弃）")
def update_factor_config_by_factor(
    config_data: FactorConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新因子配置（按因子ID，支持批量更新映射）（已废弃）
    
    注意：此接口已废弃，请使用 POST /api/v1/factor/configs/update 代替
    """
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 获取当前配置
        current_config = FactorService.get_factor_config(db, config_data.factor_id)
        
        # 如果提供了mappings，更新mappings
        if config_data.mappings is not None:
            current_config["mappings"] = [{"model_id": m.model_id, "codes": m.codes} for m in config_data.mappings]
        
        # 如果提供了enabled，更新enabled
        if config_data.enabled is not None:
            current_config["enabled"] = config_data.enabled
        
        # 使用新的update_factor_config方法
        factor_def = FactorService.update_factor_config(
            db=db,
            factor_id=config_data.factor_id,
            factor_config=current_config,
        )
        
        config = factor_def.get_factor_config()
        mappings = [FactorConfigResponse(
            id=0,  # 占位符，实际不存在
            factor_id=config_data.factor_id,
            model_id=m.get("model_id"),
            codes=m.get("codes"),
            enabled=config.get("enabled", True),
            created_time=factor_def.created_time,
            updated_time=factor_def.updated_time,
        ) for m in config.get("mappings", [])]
        
        return FactorConfigGroupedResponse(
            factor_id=config_data.factor_id,
            enabled=config.get("enabled", True),
            mappings=mappings,
            created_time=factor_def.created_time,
            updated_time=factor_def.updated_time,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"更新因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新因子配置失败")


@router.post("/configs/by-factor/delete", status_code=status.HTTP_204_NO_CONTENT, summary="删除因子配置（按因子ID，删除该因子的所有配置）（已废弃）")
def delete_factor_config_by_factor(
    request: FactorConfigDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除因子配置（按因子ID，删除该因子的所有配置）（已废弃）
    
    注意：此接口已废弃，请使用 POST /api/v1/factor/configs/delete 代替
    """
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 使用新的方法删除配置
        factor_def = FactorService.get_factor_definition(db, request.factor_id)
        factor_def.set_factor_config({})
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除因子配置失败")


@router.post("/configs/flat", response_model=FactorConfigListResponse, summary="获取因子配置列表（扁平列表）")
def list_factor_configs_flat(
    request: FactorConfigListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取因子配置列表（扁平列表，每个映射一条记录）"""
    try:
        items, total = FactorService.list_factor_configs(
            db=db,
            factor_id=request.factor_id,
            skip=request.skip,
            limit=request.limit,
            enabled=request.enabled,
            order_by=request.order_by,
            order=request.order,
        )
        return FactorConfigListResponse(items=[FactorConfigResponse.from_orm(item) for item in items], total=total)
    except Exception as e:
        logger.error(f"获取因子配置列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取因子配置列表失败")


@router.post("/configs/update_single", response_model=FactorConfigResponse, summary="更新单个因子配置")
def update_factor_config_single(
    config_data: FactorConfigSingleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新单个因子配置（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        config = FactorService.update_factor_config(
            db=db,
            config_id=config_data.config_id,
            model_id=config_data.model_id,
            codes=config_data.codes,
            enabled=config_data.enabled,
        )
        return FactorConfigResponse.from_orm(config)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新因子配置失败")


@router.post("/configs/delete_single", status_code=status.HTTP_204_NO_CONTENT, summary="删除因子配置")
def delete_factor_config_single(
    request: FactorConfigSingleDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除因子配置（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        FactorService.delete_factor_config(db, request.config_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除因子配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除因子配置失败")


# ==================== 因子计算 ====================

@router.post("/calculate", response_model=FactorCalculationResponse, summary="手动触发因子计算")
def calculate_factor(
    request: FactorCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """手动触发因子计算（需要管理员权限）"""
    if not is_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    try:
        # 从 current_user 构建 extra_info
        extra_info = {"created_by": current_user.username, "updated_by": current_user.username}
        
        result = FactorCalculationService.calculate_factor(
            db=db,
            factor_id=request.factor_id,
            codes=request.codes,
            start_date=request.start_date,
            end_date=request.end_date,
            extra_info=extra_info,
        )
        return FactorCalculationResponse(**result)
    except Exception as e:
        logger.error(f"因子计算失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="因子计算失败")


# ==================== 因子结果查询 ====================

@router.post("/results", response_model=FactorResultResponse, summary="查询因子计算结果")
def get_factor_results(
    request: FactorResultQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询因子计算结果"""
    try:
        items = FactorCalculationService.get_factor_results(
            db=db,
            code=request.code,
            factor_name=request.factor_name,
            trade_date=request.trade_date,
        )

        result_items = []

        # 如果没有指定因子名称，返回所有因子（转为长格式）
        if not request.factor_name:
            # 获取所有因子定义以进行映射
            factor_defs, _ = FactorService.list_factor_definitions(db, limit=1000)
            col_to_def = {f.column_name: f for f in factor_defs if f.column_name}
            
            # 元数据列，查询所有因子时跳过这些列
            meta_columns = {"id", "ts_code", "trade_date", "created_by", "created_time", "updated_by", "updated_time"}

            for item in items:
                # 遍历行中的所有列
                for col, val in item.items():
                    if col in meta_columns or val is None:
                        continue
                    
                    # 尝试匹配因子定义，获取显示名称
                    f_def = col_to_def.get(col)
                    display_name = f_def.factor_name if f_def else col

                    result_items.append(
                        {
                            "id": item.get("id"),
                            "trade_date": date.fromisoformat(item["trade_date"])
                            if isinstance(item["trade_date"], str)
                            else item["trade_date"],
                            "factor_name": display_name,
                            "factor_value": val,
                        }
                    )

            return FactorResultResponse(
                code=request.code,
                factor_name="all",
                items=result_items,
                total=len(result_items),
            )

        # 获取特定因子定义
        factor_def = FactorService.get_factor_definition_by_name(db, request.factor_name)
        if not factor_def:
            logger.warning(f"查询因子结果失败: 因子定义不存在 - {request.factor_name}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子定义不存在")

        # 过滤出该因子的数据
        if factor_def.factor_type == "组合因子":
            # 组合因子：返回所有不属于其他单因子的列
            factor_defs, _ = FactorService.list_factor_definitions(db, limit=1000)
            other_factor_cols = {f.column_name for f in factor_defs if f.id != factor_def.id and f.column_name}
            meta_columns = {"id", "ts_code", "trade_date", "created_by", "created_time", "updated_by", "updated_time"}
            
            for item in items:
                for col, val in item.items():
                    if col in meta_columns or col in other_factor_cols or val is None:
                        continue
                    
                    result_items.append(
                        {
                            "id": item.get("id"),
                            "trade_date": date.fromisoformat(item["trade_date"])
                            if isinstance(item["trade_date"], str)
                            else item["trade_date"],
                            "factor_name": col,
                            "factor_value": val,
                        }
                    )
        else:
            # 单因子：直接匹配列名
            column_name = factor_def.column_name
            for item in items:
                if column_name in item and item[column_name] is not None:
                    result_items.append(
                        {
                            "id": item.get("id"),
                            "trade_date": date.fromisoformat(item["trade_date"])
                            if isinstance(item["trade_date"], str)
                            else item["trade_date"],
                            "factor_name": factor_def.factor_name,
                            "factor_value": item.get(column_name),
                        }
                    )

        return FactorResultResponse(
            code=request.code,
            factor_name=request.factor_name,
            items=result_items,
            total=len(result_items),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询因子结果失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询因子结果失败")


# ==================== 量化因子查询 ====================

@router.post("/quant-factors/query", response_model=QuantFactorQueryResponse, summary="查询量化因子数据")
def query_quant_factors(
    request: QuantFactorQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    分页查询量化因子数据（通过联合视图）
    """
    try:
        items, total = FactorService.get_quant_factor_results(
            db=db,
            ts_code=request.ts_code,
            start_date=request.start_date,
            end_date=request.end_date,
            filter_conditions=request.filter_conditions,
            skip=request.skip,
            limit=request.limit,
            order_by=request.order_by,
            order=request.order or "desc",
        )
        return QuantFactorQueryResponse(items=items, total=total)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"查询量化因子数据失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询量化因子数据失败")

