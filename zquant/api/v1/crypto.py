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

"""
加密货币数据API
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from zquant.common.database import get_db
from zquant.common.response import success_response
from zquant.api.decorators import handle_data_api_error as handle_errors
from zquant.data.crypto_sync import CryptoDataSyncService
from zquant.models.crypto import (
    CryptoPair,
    create_kline_table_class,
    get_kline_table_name,
)
from zquant.repositories import CryptoPairRepository, CryptoKlineRepository


router = APIRouter(prefix="/crypto", tags=["加密货币"])


# ============== Request Models ==============


class SyncKlinesRequest(BaseModel):
    """同步K线请求"""

    symbol: str = Field(..., description="交易对符号(如BTCUSDT)")
    interval: str = Field(default="1h", description="K线周期")
    days_back: int = Field(default=7, description="回溯天数")
    start_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")


class SyncPairsRequest(BaseModel):
    """同步交易对请求"""

    quote_asset: str = Field(default="USDT", description="计价资产")
    status: str = Field(default="trading", description="交易状态")


class ExchangeConfigRequest(BaseModel):
    """交易所配置请求"""

    exchange: str = Field(..., description="交易所名称")
    api_key: str = Field(..., description="API Key")
    api_secret: str = Field(..., description="API Secret")
    passphrase: str | None = Field(default=None, description="Passphrase(OKX需要)")


# ============== API Endpoints ==============


@router.get("/pairs")
@handle_errors
async def get_crypto_pairs(
    quote_asset: str | None = Query(default=None, description="计价资产"),
    exchange: str | None = Query(default=None, description="交易所"),
    status: str = Query(default="trading", description="交易状态"),
    limit: int = Query(default=100, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    获取加密货币交易对列表
    """
    repo = CryptoPairRepository(db)
    
    # 根据条件获取交易对
    if exchange:
        pairs = repo.get_by_exchange(exchange, limit=limit)
    else:
        pairs = repo.get_all(skip=0, limit=limit)
    
    # 过滤状态
    if status:
        pairs = [p for p in pairs if p.status == status]
    
    # 过滤计价资产
    if quote_asset:
        pairs = [p for p in pairs if p.quote_asset == quote_asset]
    
    return success_response(
        data=[{
            "symbol": pair.symbol,
            "base_asset": pair.base_asset,
            "quote_asset": pair.quote_asset,
            "exchange": pair.exchange,
            "status": pair.status,
            "created_at": pair.created_at.isoformat() if pair.created_at else None,
        } for pair in pairs],
        message="获取交易对列表成功",
    )
        logger.error(f"获取交易对列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/{symbol}")
@handle_errors
async def get_crypto_klines(
    symbol: str,
    interval: str = Query(default="1h", description="K线周期"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量"),
    start_time: datetime | None = Query(default=None, description="开始时间"),
    end_time: datetime | None = Query(default=None, description="结束时间"),
    db: Session = Depends(get_db),
):
    """
    获取加密货币K线数据
    """
    repo = CryptoKlineRepository(db)
    
    # 获取K线数据
    if start_time and end_time:
        klines = repo.get_by_time_range(symbol, interval, start_time, end_time)
    else:
        klines = repo.get_latest(symbol, interval, limit)
    
    return success_response(
        data=klines,
        message=f"获取K线数据成功: {symbol}, {len(klines)}条",
    )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/pairs")
async def sync_crypto_pairs(
    request: SyncPairsRequest,
    exchange_config: ExchangeConfigRequest,
    db: Session = Depends(get_db),
):
    """
    同步交易对列表
    """
    try:
        # 创建同步服务
        sync_service = CryptoDataSyncService(
            db_session=db,
            exchange_name=exchange_config.exchange,
            api_key=exchange_config.api_key,
            api_secret=exchange_config.api_secret,
            passphrase=exchange_config.passphrase,
        )
        
        # 同步交易对
        count = sync_service.sync_pairs(
            quote_asset=request.quote_asset,
            status=request.status,
        )
        
        return success_response(
            data={"synced_count": count},
            message=f"同步交易对完成: {count}个",
        )
        
    except Exception as e:
        logger.error(f"同步交易对失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/klines")
async def sync_crypto_klines(
    request: SyncKlinesRequest,
    exchange_config: ExchangeConfigRequest,
    db: Session = Depends(get_db),
):
    """
    同步K线数据
    """
    try:
        # 创建同步服务
        sync_service = CryptoDataSyncService(
            db_session=db,
            exchange_name=exchange_config.exchange,
            api_key=exchange_config.api_key,
            api_secret=exchange_config.api_secret,
            passphrase=exchange_config.passphrase,
        )
        
        # 同步K线
        count = sync_service.sync_klines(
            symbol=request.symbol,
            interval=request.interval,
            start_time=request.start_time,
            end_time=request.end_time,
        )
        
        return success_response(
            data={"synced_count": count},
            message=f"同步K线完成: {count}条",
        )
        
    except Exception as e:
        logger.error(f"同步K线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol}")
async def get_crypto_ticker(
    symbol: str,
    exchange: str = Query(default="binance", description="交易所"),
    db: Session = Depends(get_db),
):
    """
    获取实时行情(从数据库最新K线)
    """
    try:
        # 从1小时K线获取最新数据
        KlineTable = create_kline_table_class("1h")
        
        latest_kline = (
            db.query(KlineTable)
            .filter_by(symbol=symbol)
            .order_by(KlineTable.timestamp.desc())
            .first()
        )
        
        if not latest_kline:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的数据")
        
        return success_response(
            data={
                "symbol": symbol,
                "exchange": exchange,
                "price": latest_kline.close,
                "timestamp": latest_kline.timestamp.isoformat(),
                "open": latest_kline.open,
                "high": latest_kline.high,
                "low": latest_kline.low,
                "close": latest_kline.close,
                "volume": latest_kline.volume,
            },
            message="获取行情成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intervals")
async def get_supported_intervals():
    """
    获取支持的K线周期列表
    """
    return success_response(
        data={
            "intervals": CryptoDataSyncService.SUPPORTED_INTERVALS,
            "description": {
                "1m": "1分钟",
                "5m": "5分钟",
                "15m": "15分钟",
                "30m": "30分钟",
                "1h": "1小时",
                "4h": "4小时",
                "1d": "1天",
                "1w": "1周",
            }
        },
        message="获取支持的K线周期成功",
    )
