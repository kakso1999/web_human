"""
认证中间件
处理请求认证和用户信息注入
"""
from typing import Optional, List
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security.jwt import verify_access_token, TokenPayload
from core.exceptions.handlers import (
    UnauthorizedException,
    TokenExpiredException,
    TokenInvalidException,
    PermissionDeniedException
)

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenPayload]:
    """
    从请求中提取并验证 Token

    Args:
        credentials: HTTP 认证凭据

    Returns:
        Token 载荷或 None
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)

    return payload


async def get_current_user_id(
    payload: Optional[TokenPayload] = Depends(get_token_payload)
) -> str:
    """
    获取当前用户 ID（必须登录）

    Args:
        payload: Token 载荷

    Returns:
        用户 ID

    Raises:
        UnauthorizedException: 未登录
        TokenInvalidException: Token 无效
    """
    if not payload:
        raise UnauthorizedException("请先登录")

    return payload.sub


async def get_current_user_optional(
    payload: Optional[TokenPayload] = Depends(get_token_payload)
) -> Optional[str]:
    """
    获取当前用户 ID（可选，不强制登录）

    Args:
        payload: Token 载荷

    Returns:
        用户 ID 或 None
    """
    if payload:
        return payload.sub
    return None


def require_roles(*allowed_roles: str):
    """
    角色权限检查装饰器

    Args:
        allowed_roles: 允许的角色列表

    Returns:
        依赖函数
    """
    async def role_checker(
        payload: Optional[TokenPayload] = Depends(get_token_payload)
    ) -> TokenPayload:
        if not payload:
            raise UnauthorizedException("请先登录")

        if payload.role not in allowed_roles:
            raise PermissionDeniedException(
                f"需要以下角色之一: {', '.join(allowed_roles)}"
            )

        return payload

    return role_checker


# 预定义的角色检查器
require_admin = require_roles("admin", "super")
require_super = require_roles("super")
require_subscriber = require_roles("subscriber", "admin", "super")


class RoleChecker:
    """角色检查器类"""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        payload: Optional[TokenPayload] = Depends(get_token_payload)
    ) -> TokenPayload:
        if not payload:
            raise UnauthorizedException("请先登录")

        if payload.role not in self.allowed_roles:
            raise PermissionDeniedException(
                f"需要以下角色之一: {', '.join(self.allowed_roles)}"
            )

        return payload
