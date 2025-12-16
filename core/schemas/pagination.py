"""
分页模型
统一分页请求和响应格式
"""
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """分页请求参数"""
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")

    @property
    def skip(self) -> int:
        """计算跳过数量"""
        return (self.page - 1) * self.page_size


class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""
    items: List[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        """总页数"""
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    code: int = 0
    message: str = "success"
    data: Optional[PaginatedData[T]] = None


def paginate(
    items: List[T],
    total: int,
    page: int,
    page_size: int
) -> dict:
    """
    创建分页响应数据

    Args:
        items: 数据列表
        total: 总数量
        page: 当前页码
        page_size: 每页数量

    Returns:
        分页响应字典
    """
    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }
