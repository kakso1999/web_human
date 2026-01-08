"""
User 模块 - Schema 定义
用户信息相关的请求和响应模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class UserProfile(BaseModel):
    """用户资料详情

    包含用户的完整个人信息，用于个人中心展示。
    """
    id: str = Field(..., description="用户唯一标识ID")
    email: str = Field(..., description="用户邮箱")
    nickname: str = Field(..., description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像图片URL")
    role: str = Field(..., description="用户角色：user/subscriber/admin/super")
    subscription: dict = Field(..., description="订阅信息，包含plan和expires_at")
    is_active: bool = Field(..., description="账号是否激活")
    created_at: datetime = Field(..., description="注册时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "6948bda91fd873cf81f5addd",
                "email": "user@example.com",
                "nickname": "小明",
                "avatar_url": "https://example.com/avatar.jpg",
                "role": "user",
                "subscription": {
                    "plan": "free",
                    "expires_at": None
                },
                "is_active": True,
                "created_at": "2025-01-01T12:00:00"
            }
        }
    )


class UpdateProfileRequest(BaseModel):
    """更新用户资料请求

    用于修改用户的个人信息，如昵称等。
    所有字段都是可选的，只更新提供的字段。
    """
    nickname: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="新昵称，2-50个字符，支持中文、字母、数字和下划线",
        json_schema_extra={"example": "新昵称"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nickname": "新昵称"
            }
        }
    )

    @field_validator('nickname')
    @classmethod
    def validate_nickname(cls, v):
        if v and not re.match(r'^[\w\u4e00-\u9fa5]+$', v):
            raise ValueError('昵称只能包含字母、数字、中文和下划线')
        return v


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
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserListItem(BaseModel):
    """用户列表项

    管理后台用户列表中的单条用户信息。
    """
    id: str = Field(..., description="用户唯一标识ID")
    email: str = Field(..., description="用户邮箱")
    nickname: str = Field(..., description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像图片URL")
    role: str = Field(..., description="用户角色")
    subscription_plan: str = Field(..., description="订阅计划：free/basic/premium")
    is_active: bool = Field(..., description="账号是否激活")
    created_at: datetime = Field(..., description="注册时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "6948bda91fd873cf81f5addd",
                "email": "user@example.com",
                "nickname": "小明",
                "avatar_url": "https://example.com/avatar.jpg",
                "role": "user",
                "subscription_plan": "free",
                "is_active": True,
                "created_at": "2025-01-01T12:00:00",
                "last_login_at": "2025-01-15T08:30:00"
            }
        }
    )
