"""
Auth 模块 - Schema 定义
登录、注册、Token 相关的请求和响应模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re


class RegisterRequest(BaseModel):
    """用户注册请求

    用于新用户注册账号，需要提供邮箱、密码和昵称。
    密码必须包含大小写字母和数字，长度8-128位。
    """
    email: EmailStr = Field(
        ...,
        description="用户邮箱地址，用于登录和接收通知",
        json_schema_extra={"example": "user@example.com"}
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="登录密码，至少8位，必须包含大小写字母和数字",
        json_schema_extra={"example": "MyPassword123"}
    )
    nickname: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="用户昵称，2-50个字符，支持中文、字母、数字和下划线",
        json_schema_extra={"example": "小明"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "MyPassword123",
                "nickname": "小明"
            }
        }
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """密码强度验证"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v

    @field_validator('nickname')
    @classmethod
    def validate_nickname(cls, v):
        """昵称验证"""
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', v):
            raise ValueError('昵称只能包含字母、数字、中文和下划线')
        return v


class LoginRequest(BaseModel):
    """用户登录请求

    使用邮箱和密码进行登录认证。
    登录成功后返回访问令牌和刷新令牌。
    """
    email: EmailStr = Field(
        ...,
        description="注册时使用的邮箱地址",
        json_schema_extra={"example": "user@example.com"}
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="用户密码",
        json_schema_extra={"example": "MyPassword123"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "MyPassword123"
            }
        }
    )


class TokenResponse(BaseModel):
    """令牌响应

    包含访问令牌和刷新令牌，用于API认证。
    访问令牌有效期较短（默认2小时），刷新令牌有效期较长（默认7天）。
    """
    access_token: str = Field(..., description="访问令牌，用于API请求认证")
    refresh_token: str = Field(..., description="刷新令牌，用于获取新的访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型，固定为bearer")
    expires_in: int = Field(..., description="访问令牌有效期（秒）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 7200
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求

    使用刷新令牌获取新的访问令牌。
    当访问令牌过期时调用此接口。
    """
    refresh_token: str = Field(
        ...,
        description="之前获取的刷新令牌",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )


class UserResponse(BaseModel):
    """用户信息响应

    返回用户的基本信息，不包含敏感数据（如密码）。
    """
    id: str = Field(..., description="用户唯一标识ID")
    email: str = Field(..., description="用户邮箱")
    nickname: str = Field(..., description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="用户头像URL")
    role: str = Field(..., description="用户角色：user/subscriber/admin/super")
    is_active: bool = Field(..., description="账号是否激活")
    created_at: datetime = Field(..., description="账号创建时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "6948bda91fd873cf81f5addd",
                "email": "user@example.com",
                "nickname": "小明",
                "avatar_url": "https://example.com/avatar.jpg",
                "role": "user",
                "is_active": True,
                "created_at": "2025-01-01T12:00:00"
            }
        }
    )


class LoginResponse(BaseModel):
    """登录响应

    登录成功后返回用户信息和令牌。
    """
    user: UserResponse = Field(..., description="用户基本信息")
    tokens: TokenResponse = Field(..., description="认证令牌")


class GoogleAuthRequest(BaseModel):
    """Google OAuth 认证请求

    使用 Google 授权码进行登录或注册。
    授权码从 Google OAuth 回调中获取。
    """
    code: str = Field(
        ...,
        description="Google OAuth 授权码",
        json_schema_extra={"example": "4/0AX4XfWh..."}
    )


class GoogleUserInfo(BaseModel):
    """Google 用户信息

    从 Google API 获取的用户基本信息。
    """
    id: str = Field(..., description="Google 用户ID")
    email: str = Field(..., description="Google 账号邮箱")
    name: Optional[str] = Field(None, description="用户显示名称")
    picture: Optional[str] = Field(None, description="Google 头像URL")
    verified_email: bool = Field(default=False, description="邮箱是否已验证")


class ChangePasswordRequest(BaseModel):
    """修改密码请求

    用户修改自己的登录密码。
    需要提供旧密码进行验证，新密码需要满足强度要求。
    """
    old_password: str = Field(
        ...,
        min_length=1,
        description="当前密码",
        json_schema_extra={"example": "OldPassword123"}
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="新密码，至少8位，必须包含大小写字母和数字",
        json_schema_extra={"example": "NewPassword456"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "old_password": "OldPassword123",
                "new_password": "NewPassword456"
            }
        }
    )

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """密码强度验证"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """密码强度验证"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v
