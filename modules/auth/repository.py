"""
Auth 模块 - 数据访问层
用户认证相关的数据库操作
"""
from typing import Optional, Dict, Any
from datetime import datetime

from core.database.base_repository import BaseRepository
from core.security.password import hash_password


class UserRepository(BaseRepository):
    """用户数据仓储"""

    collection_name = "users"

    async def create_user(
        self,
        email: str,
        password: str,
        nickname: str,
        role: str = "user",
        google_id: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> str:
        """
        创建用户

        Args:
            email: 邮箱
            password: 明文密码（将被哈希）
            nickname: 昵称
            role: 角色
            google_id: Google 账号 ID
            avatar_url: 头像 URL

        Returns:
            用户 ID
        """
        user_data = {
            "email": email.lower(),
            "password_hash": hash_password(password) if password else None,
            "nickname": nickname,
            "role": role,
            "avatar_url": avatar_url,
            "google_id": google_id,
            "subscription": {
                "plan": "free",
                "expires_at": None
            },
            "is_active": True,
            "email_verified": google_id is not None,  # Google 登录默认已验证
            "last_login_at": None,
        }

        return await self.create(user_data)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        return await self.get_one({"email": email.lower()})

    async def get_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """根据 Google ID 获取用户"""
        return await self.get_one({"google_id": google_id})

    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        return await self.exists({"email": email.lower()})

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """更新密码"""
        return await self.update(user_id, {
            "password_hash": hash_password(new_password)
        })

    async def update_last_login(self, user_id: str) -> bool:
        """更新最后登录时间"""
        return await self.update(user_id, {
            "last_login_at": datetime.utcnow()
        })

    async def link_google_account(
        self,
        user_id: str,
        google_id: str,
        avatar_url: Optional[str] = None
    ) -> bool:
        """关联 Google 账号"""
        update_data = {"google_id": google_id}
        if avatar_url:
            update_data["avatar_url"] = avatar_url
        return await self.update(user_id, update_data)

    async def set_email_verified(self, user_id: str) -> bool:
        """设置邮箱已验证"""
        return await self.update(user_id, {"email_verified": True})

    async def set_active(self, user_id: str, is_active: bool) -> bool:
        """设置用户激活状态"""
        return await self.update(user_id, {"is_active": is_active})
