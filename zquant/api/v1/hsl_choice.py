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

from datetime import date

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from zquant.api.deps import get_current_user, get_db
from zquant.models.user import User
from zquant.schemas.common import Pagination
from zquant.schemas.hsl_choice import HslChoiceQueryRequest, HslChoiceRequest, HslChoiceResponse
from zquant.services.hsl_choice import HslChoiceService

router = APIRouter()


@router.post("", response_model=Pagination[HslChoiceResponse])
def query_hsl_choice(
    request: HslChoiceQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询ZQ精选数据
    """
    page = request.page
    page_size = request.page_size
    skip = (page - 1) * page_size
    
    items, total = HslChoiceService.query_hsl_choice(
        db=db,
        trade_date_start=request.start_date,
        trade_date_end=request.end_date,
        ts_code=request.ts_code,
        code=request.code,
        name=request.name,
        skip=skip,
        limit=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/add", response_model=dict)
def add_hsl_choice(
    request: HslChoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    添加ZQ精选数据
    """
    count = HslChoiceService.add_hsl_choice(
        db=db,
        trade_date=request.trade_date,
        ts_codes=request.ts_codes,
        username=current_user.username,
    )
    return {"message": "添加成功", "count": count}
