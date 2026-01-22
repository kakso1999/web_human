"""
并发控制工具
阿里云 API 最大支持 5 个并发任务
"""

import asyncio
from typing import Any, Callable, Coroutine, List, TypeVar
from functools import wraps

# 全局信号量：限制并发数为 5
_cloud_api_semaphore = asyncio.Semaphore(5)

T = TypeVar('T')


async def run_with_limit(coro: Coroutine[Any, Any, T]) -> T:
    """
    使用信号量限制并发执行

    Args:
        coro: 要执行的协程

    Returns:
        协程的返回值
    """
    async with _cloud_api_semaphore:
        return await coro


async def run_batch_with_limit(
    tasks: List[Coroutine[Any, Any, T]],
    max_concurrent: int = 5
) -> List[T]:
    """
    批量执行任务，限制并发数

    Args:
        tasks: 协程列表
        max_concurrent: 最大并发数

    Returns:
        结果列表（保持顺序）
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_one(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*[run_one(task) for task in tasks])


def cloud_api_limit(func: Callable) -> Callable:
    """
    装饰器：为云端 API 调用添加并发限制

    用法:
        @cloud_api_limit
        async def call_cosyvoice_api(...):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with _cloud_api_semaphore:
            return await func(*args, **kwargs)
    return wrapper


class CloudAPIExecutor:
    """
    云端 API 执行器

    管理并发执行和费用统计
    """

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.total_cost = 0.0
        self._lock = asyncio.Lock()

    async def execute(self, coro: Coroutine[Any, Any, T]) -> T:
        """执行单个任务"""
        async with self.semaphore:
            return await coro

    async def execute_batch(self, tasks: List[Coroutine[Any, Any, T]]) -> List[T]:
        """批量执行任务"""
        async def run_one(coro):
            async with self.semaphore:
                return await coro

        return await asyncio.gather(*[run_one(task) for task in tasks])

    async def add_cost(self, cost: float):
        """累加费用"""
        async with self._lock:
            self.total_cost += cost

    def get_total_cost(self) -> float:
        """获取总费用"""
        return self.total_cost

    def reset(self):
        """重置费用统计"""
        self.total_cost = 0.0


# 全局执行器实例
cloud_executor = CloudAPIExecutor(max_concurrent=5)
