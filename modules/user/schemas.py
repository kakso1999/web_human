"""
User 模块 - Schema 定义
用户信息相关的请求和响应模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class UserProfile(BaseModel):
    """用户资料"""
    id: str
    email: str
    nickname: str
    avatar_url: Optional[str] = None
    role: str
    subscription: dict
    is_active: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    """更新资料请求"""
    nickname: Optional[str] = Field(None, min_length=2, max_length=50)

    @field_validator('nickname')
    @classmethod
    def validate_nickname(cls, v):
        if v and not re.match(r'^[\w\u4e00-\u9fa5]+$', v):
            raise ValueError('昵称只能包含字母、数字、中文和下划线')
        return v


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

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
    """用户列表项（管理后台用）"""
    id: str
    email: str
    nickname: str
    avatar_url: Optional[str] = None
    role: str
    subscription_plan: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
