"""
请求日志中间件
记录所有 API 请求
"""
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.config.settings import get_settings

settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求 ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 记录开始时间
        start_time = time.time()

        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # 打印日志（DEBUG 模式）
        if settings.DEBUG:
            status_code = response.status_code
            method = request.method
            path = request.url.path

            # 根据状态码着色
            if status_code >= 500:
                status_color = "\033[91m"  # 红色
            elif status_code >= 400:
                status_color = "\033[93m"  # 黄色
            else:
                status_color = "\033[92m"  # 绿色

            reset_color = "\033[0m"

            print(
                f"[{request_id}] {method} {path} - "
                f"{status_color}{status_code}{reset_color} - "
                f"{process_time:.4f}s - {client_ip}"
            )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 优先从代理头获取
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 直接连接 IP
        if request.client:
            return request.client.host

        return "unknown"
