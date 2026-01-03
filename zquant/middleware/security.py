# Copyright 2025 ZQuant Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
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
安全中间件

提供安全相关的中间件，包括CORS、XSS防护、CSRF防护等。
"""

from collections.abc import Callable
import re

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from zquant.config import settings


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF防护中间件
    
    为关键操作（POST、PUT、DELETE、PATCH）添加CSRF token验证。
    注意：这是一个简化实现，生产环境建议使用更完善的CSRF库。
    """
    
    # 需要CSRF验证的HTTP方法
    PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
    
    # 排除CSRF验证的路径（如健康检查、公开API等）
    EXCLUDED_PATHS = {
        "/health",
        "/",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并验证CSRF token
        
        注意：当前实现为简化版，主要记录警告。
        完整实现需要：
        1. 生成CSRF token并存储在session或cookie中
        2. 前端在请求头中携带CSRF token
        3. 验证token是否匹配
        """
        # 跳过排除的路径
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # 跳过 OPTIONS 请求（CORS 预检请求）
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # 只对受保护的方法进行验证
        if request.method in self.PROTECTED_METHODS:
            # 检查是否有 Authorization 头（JWT 请求通常是安全的，不受 CSRF 影响）
            if request.headers.get("Authorization"):
                return await call_next(request)

            # 检查是否有CSRF token（从请求头或表单中）
            csrf_token = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
            
            # 如果没有token，记录警告（生产环境应该拒绝请求）
            if not csrf_token:
                logger.warning(
                    f"CSRF保护: {request.method} {request.url.path} 缺少CSRF token "
                    f"(来源: {request.client.host if request.client else 'unknown'})"
                )
                # 注意：这里只记录警告，不拒绝请求，因为需要前端配合实现完整的CSRF机制
                # 生产环境应该取消注释下面的代码来拒绝请求
                # from fastapi import HTTPException, status
                # raise HTTPException(
                #     status_code=status.HTTP_403_FORBIDDEN,
                #     detail="缺少CSRF token"
                # )
        
        response = await call_next(request)
        
        # 为响应添加CSRF token（如果使用cookie存储）
        # 这里简化处理，实际应该生成token并设置到cookie或响应头中
        # response.set_cookie("csrf_token", generate_csrf_token(), httponly=False, samesite="strict")
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件

    添加安全相关的HTTP响应头，增强系统安全性。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并添加安全响应头"""
        # 跳过 OPTIONS 请求（CORS 预检请求）
        if request.method == "OPTIONS":
            return await call_next(request)

        response = await call_next(request)

        # 添加安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 如果使用HTTPS，添加HSTS头
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """
    XSS防护中间件

    清理请求参数中的潜在XSS攻击代码。
    """

    # XSS攻击模式（简化版，实际应该使用更完善的库）
    XSS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),  # 事件处理器，如onclick=
        re.compile(r"<iframe[^>]*>", re.IGNORECASE),
        re.compile(r"<object[^>]*>", re.IGNORECASE),
        re.compile(r"<embed[^>]*>", re.IGNORECASE),
    ]

    def _sanitize_value(self, value: str) -> str:
        """
        清理单个值

        Args:
            value: 待清理的值

        Returns:
            清理后的值
        """
        if not isinstance(value, str):
            return value

        # 检查是否包含XSS攻击模式
        for pattern in self.XSS_PATTERNS:
            if pattern.search(value):
                logger.warning(f"检测到潜在的XSS攻击: {value[:100]}")
                # 移除危险内容
                value = pattern.sub("", value)

        return value

    def _sanitize_dict(self, data: dict) -> dict:
        """
        递归清理字典中的值

        Args:
            data: 待清理的字典

        Returns:
            清理后的字典
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_value(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_value(item)
                    if isinstance(item, str)
                    else self._sanitize_dict(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并清理潜在的XSS攻击代码

        注意：此中间件只做基本防护，完整的XSS防护应该在输出时进行。
        """
        # 跳过 OPTIONS 请求（CORS 预检请求）
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # 清理查询参数
        if request.query_params:
            sanitized_params = self._sanitize_dict(dict(request.query_params))
            # 注意：FastAPI的query_params是只读的，这里只是记录日志
            if sanitized_params != dict(request.query_params):
                logger.warning(f"检测到查询参数中的潜在XSS攻击: {request.url.path}")
        
        # 清理请求体（JSON、表单数据）
        # 注意：FastAPI会自动解析请求体，我们需要在路由处理之前检查
        # 这里我们记录警告，实际清理应该在路由层进行
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                # JSON请求体会在路由中解析，这里只记录
                # 实际清理应该在Pydantic模型验证时进行
                pass
            elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                # 表单数据会在路由中解析，这里只记录
                pass

        response = await call_next(request)
        return response


def setup_cors_middleware(app):
    """
    设置CORS中间件

    Args:
        app: FastAPI应用实例
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if hasattr(settings, "CORS_ORIGINS") else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
