"""
User 模块 - 数据访问层
"""
from typing import Optional, Dict, Any, List
from core.database.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """用户数据仓储"""

    collection_name = "users"

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户资料"""
        return await self.get_by_id(user_id)

    async def update_profile(self, user_id: str, data: Dict[str, Any]) -> bool:
        """更新用户资料"""
        return await self.update(user_id, data)

    async def update_avatar(self, user_id: str, avatar_url: str) -> bool:
        """更新头像"""
        return await self.update(user_id, {"avatar_url": avatar_url})

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取用户列表（管理后台用）"""
        filter = {}

        if role:
            filter["role"] = role

        if is_active is not None:
            filter["is_active"] = is_active

        if search:
            filter["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"nickname": {"$regex": search, "$options": "i"}}
            ]

        return await self.get_many(
            filter=filter,
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )

    async def count_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """统计用户数量"""
        filter = {}

        if role:
            filter["role"] = role

        if is_active is not None:
            filter["is_active"] = is_active

        if search:
            filter["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"nickname": {"$regex": search, "$options": "i"}}
            ]

        return await self.count(filter)
