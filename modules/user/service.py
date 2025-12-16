"""
User 模块 - 业务逻辑层
"""
from typing import Optional
from core.security.password import verify_password, hash_password
from core.exceptions.handlers import AppException, NotFoundException
from core.schemas.base import ErrorCode

from modules.user.repository import UserRepository
from modules.user.schemas import UserProfile, UpdateProfileRequest


class UserService:
    """用户服务"""

    def __init__(self):
        self.user_repo = UserRepository()

    async def get_profile(self, user_id: str) -> UserProfile:
        """获取用户资料"""
        user = await self.user_repo.get_user_profile(user_id)

        if not user:
            raise NotFoundException("用户不存在")

        return UserProfile(
            id=user["id"],
            email=user["email"],
            nickname=user["nickname"],
            avatar_url=user.get("avatar_url"),
            role=user["role"],
            subscription=user.get("subscription", {"plan": "free"}),
            is_active=user.get("is_active", True),
            created_at=user["created_at"]
        )

    async def update_profile(
        self,
        user_id: str,
        data: UpdateProfileRequest
    ) -> UserProfile:
        """更新用户资料"""
        update_data = data.model_dump(exclude_none=True)

        if update_data:
            await self.user_repo.update_profile(user_id, update_data)

        return await self.get_profile(user_id)

    async def update_avatar(self, user_id: str, avatar_url: str) -> UserProfile:
        """更新头像"""
        await self.user_repo.update_avatar(user_id, avatar_url)
        return await self.get_profile(user_id)

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """修改密码"""
        user = await self.user_repo.get_user_profile(user_id)

        if not user:
            raise NotFoundException("用户不存在")

        # 验证旧密码
        if not user.get("password_hash"):
            raise AppException(
                code=ErrorCode.INVALID_PASSWORD,
                message="该账号使用第三方登录，无法修改密码"
            )

        if not verify_password(old_password, user["password_hash"]):
            raise AppException(
                code=ErrorCode.INVALID_PASSWORD,
                message="原密码错误"
            )

        # 更新密码
        await self.user_repo.update_profile(user_id, {
            "password_hash": hash_password(new_password)
        })

        return True


_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """获取用户服务"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
