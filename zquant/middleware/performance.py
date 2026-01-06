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
性能监控中间件
"""

import time
from collections import defaultdict
from typing import Dict, Any
from fastapi import Request, Response
from loguru import logger


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        # 性能数据存储
        self.request_times: Dict[str, list] = defaultdict(list)
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)

        # 慢查询阈值(毫秒)
        self.slow_threshold = 1000

    def record_request(self, path: str, method: str, duration: float, status_code: int):
        """
        记录请求性能数据

        Args:
            path: 请求路径
            method: 请求方法
            duration: 执行时间(秒)
            status_code: HTTP状态码
        """
        key = f"{method} {path}"

        self.request_times[key].append(duration * 1000)  # 转换为毫秒
        self.request_counts[key] += 1

        if status_code >= 400:
            self.error_counts[key] += 1

        # 慢查询警告
        if duration * 1000 > self.slow_threshold:
            logger.warning(
                f"慢查询警告 [{key}]: "
                f"执行时间={duration * 1000:.2f}ms, "
                f"状态码={status_code}"
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息

        Returns:
            统计数据
        """
        stats = {}

        for key, times in self.request_times.items():
            if not times:
                continue

            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            count = self.request_counts[key]
            error_count = self.error_counts[key]

            stats[key] = {
                'count': count,
                'avg_time_ms': round(avg_time, 2),
                'max_time_ms': round(max_time, 2),
                'min_time_ms': round(min_time, 2),
                'error_count': error_count,
                'error_rate': round(error_count / count * 100, 2) if count > 0 else 0,
            }

        return stats

    def reset(self):
        """重置统计数据"""
        self.request_times.clear()
        self.request_counts.clear()
        self.error_counts.clear()


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


async def performance_middleware(request: Request, call_next):
    """
    性能监控中间件

    记录每个请求的执行时间和状态码
    """
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 计算执行时间
    duration = time.time() - start_time

    # 记录性能数据
    path = request.url.path
    method = request.method
    status_code = response.status_code

    performance_monitor.record_request(path, method, duration, status_code)

    # 添加性能头
    response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"

    return response


def get_performance_stats() -> Dict[str, Any]:
    """
    获取性能统计数据

    Returns:
        统计数据
    """
    return performance_monitor.get_stats()


def reset_performance_stats():
    """重置性能统计数据"""
    performance_monitor.reset()
