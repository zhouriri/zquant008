from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class HslChoiceQueryRequest(BaseModel):
    """查询ZQ精选数据请求"""
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    ts_code: str | None = Field(None, description="TS代码")
    code: str | None = Field(None, description="股票代码")
    name: str | None = Field(None, description="股票名称")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class HslChoiceRequest(BaseModel):
    """添加ZQ精选数据请求"""
    trade_date: date = Field(..., description="交易日期")
    ts_codes: list[str] = Field(..., description="股票代码列表")


class HslChoiceResponse(BaseModel):
    """ZQ精选数据响应"""
    id: int
    trade_date: date
    ts_code: str
    code: str
    name: str | None = None
    created_by: str | None = None
    created_time: datetime | None = None
    updated_by: str | None = None
    updated_time: datetime | None = None

    class Config:
        from_attributes = True
