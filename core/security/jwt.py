"""
JWT 令牌处理模块
双 Token 机制：Access Token + Refresh Token
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import jwt, JWTError
from pydantic import BaseModel

from core.config.settings import get_settings

settings = get_settings()


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str  # 用户 ID
    exp: datetime  # 过期时间
    iat: datetime  # 签发时间
    jti: str  # Token ID (用于黑名单)
    type: str  # "access" 或 "refresh"
    role: str  # 用户角色


class TokenPair(BaseModel):
    """Token 对"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access Token 过期秒数


def create_access_token(user_id: str, role: str) -> str:
    """
    创建访问令牌

    Args:
        user_id: 用户 ID
        role: 用户角色

    Returns:
        Access Token 字符串
    """
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "role": role
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str, role: str) -> str:
    """
    创建刷新令牌

    Args:
        user_id: 用户 ID
        role: 用户角色

    Returns:
        Refresh Token 字符串
    """
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
        "role": role
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_token_pair(user_id: str, role: str) -> TokenPair:
    """
    创建 Token 对

    Args:
        user_id: 用户 ID
        role: 用户角色

    Returns:
        TokenPair 对象
    """
    return TokenPair(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id, role),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    解码并验证令牌

    Args:
        token: Token 字符串

    Returns:
        TokenPayload 或 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[TokenPayload]:
    """
    验证 Access Token

    Args:
        token: Token 字符串

    Returns:
        TokenPayload 或 None (如果无效或不是 access token)
    """
    payload = decode_token(token)
    if payload and payload.type == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[TokenPayload]:
    """
    验证 Refresh Token

    Args:
        token: Token 字符串

    Returns:
        TokenPayload 或 None (如果无效或不是 refresh token)
    """
    payload = decode_token(token)
    if payload and payload.type == "refresh":
        return payload
    return None
