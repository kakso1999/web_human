"""
Digital Human Repository - 数据访问层
数字人头像档案的 MongoDB 操作
"""

from datetime import datetime
from typing import List, Optional
from bson import ObjectId

from core.database.mongodb import get_database


class AvatarProfileRepository:
    """数字人头像档案数据访问"""

    def __init__(self):
        self.collection_name = "avatar_profiles"

    @property
    def collection(self):
        db = get_database()
        return db[self.collection_name]

    async def create(self, profile_data: dict) -> str:
        """创建头像档案"""
        profile_data["created_at"] = datetime.utcnow()
        profile_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(profile_data)
        return str(result.inserted_id)

    async def get_by_id(self, profile_id: str) -> Optional[dict]:
        """根据ID获取头像档案"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(profile_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    async def get_by_user_id(self, user_id: str, include_deleted: bool = False) -> List[dict]:
        """获取用户的所有头像档案"""
        query = {"user_id": user_id}
        if not include_deleted:
            query["status"] = "active"

        cursor = self.collection.find(query).sort("created_at", -1)
        profiles = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            profiles.append(doc)
        return profiles

    async def update(self, profile_id: str, update_data: dict) -> bool:
        """更新头像档案"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(profile_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete(self, profile_id: str) -> bool:
        """软删除头像档案"""
        return await self.update(profile_id, {"status": "deleted"})

    async def count_by_user(self, user_id: str) -> int:
        """统计用户的头像档案数量"""
        return await self.collection.count_documents({
            "user_id": user_id,
            "status": "active"
        })


# 全局实例
avatar_profile_repository = AvatarProfileRepository()
