from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class HslChoiceQueryRequest(BaseModel):
    """查询ZQ精选数据请求"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    ts_code: Optional[str] = Field(None, description="TS代码")
    code: Optional[str] = Field(None, description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class HslChoiceRequest(BaseModel):
    """添加ZQ精选数据请求"""
    trade_date: date = Field(..., description="交易日期")
    ts_codes: List[str] = Field(..., description="股票代码列表")


class HslChoiceResponse(BaseModel):
    """ZQ精选数据响应"""
    id: int
    trade_date: date
    ts_code: str
    code: str
    name: Optional[str] = None
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_time: Optional[datetime] = None

    class Config:
        from_attributes = True
