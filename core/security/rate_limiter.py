"""
请求限流模块
使用 Redis 实现滑动窗口限流
"""
import time
from typing import Optional

from redis import asyncio as aioredis

from core.config.settings import get_settings

settings = get_settings()


class RateLimiter:
    """滑动窗口限流器"""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """
        初始化限流器

        Args:
            redis_client: Redis 客户端
        """
        self.redis = redis_client
        self._connected = False

    async def connect(self) -> None:
        """连接 Redis"""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        self._connected = True

    async def disconnect(self) -> None:
        """断开 Redis 连接"""
        if self.redis:
            await self.redis.close()
            self._connected = False

    async def is_rate_limited(
        self,
        key: str,
        limit: int = None,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        检查是否被限流

        Args:
            key: 限流键（如 user_id 或 IP）
            limit: 窗口内最大请求数，默认使用配置
            window: 时间窗口（秒）

        Returns:
            (是否被限流, 剩余请求数)
        """
        if not self._connected:
            await self.connect()

        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        current_time = int(time.time())
        window_start = current_time - window

        rate_key = f"rate_limit:{key}"

        pipe = self.redis.pipeline()

        # 移除窗口外的请求
        pipe.zremrangebyscore(rate_key, 0, window_start)
        # 添加当前请求
        pipe.zadd(rate_key, {str(current_time): current_time})
        # 获取窗口内请求数
        pipe.zcard(rate_key)
        # 设置过期时间
        pipe.expire(rate_key, window)

        results = await pipe.execute()
        request_count = results[2]
        remaining = max(0, limit - request_count)

        return request_count > limit, remaining

    async def get_remaining(self, key: str, limit: int = None, window: int = 60) -> int:
        """
        获取剩余请求数

        Args:
            key: 限流键
            limit: 窗口内最大请求数
            window: 时间窗口（秒）

        Returns:
            剩余请求数
        """
        if not self._connected:
            await self.connect()

        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        current_time = int(time.time())
        window_start = current_time - window

        rate_key = f"rate_limit:{key}"

        # 清理过期数据
        await self.redis.zremrangebyscore(rate_key, 0, window_start)
        # 获取当前计数
        count = await self.redis.zcard(rate_key)

        return max(0, limit - count)


# 全局限流器实例
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """获取限流器单例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        await _rate_limiter.connect()
    return _rate_limiter
