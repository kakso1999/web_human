"""
Story 模块 - 数据访问层
"""
from typing import Optional, Dict, Any, List
from core.database.base_repository import BaseRepository


class CategoryRepository(BaseRepository):
    """分类数据仓储"""

    collection_name = "categories"

    async def list_all(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        return await self.get_many(sort=[("sort_order", 1)])

    async def increment_story_count(self, category_id: str, delta: int = 1) -> bool:
        """更新分类的故事数量"""
        from core.config.database import Database
        result = await Database.get_collection(self.collection_name).update_one(
            {"_id": category_id},
            {"$inc": {"story_count": delta}}
        )
        return result.modified_count > 0


class StoryRepository(BaseRepository):
    """故事数据仓储"""

    collection_name = "stories"

    async def list_stories(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[str] = None,
        is_published: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取故事列表"""
        filter = {}

        if category_id:
            filter["category_id"] = category_id

        if is_published is not None:
            filter["is_published"] = is_published

        if search:
            filter["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"title_en": {"$regex": search, "$options": "i"}}
            ]

        return await self.get_many(
            filter=filter,
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )

    async def count_stories(
        self,
        category_id: Optional[str] = None,
        is_published: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """统计故事数量"""
        filter = {}

        if category_id:
            filter["category_id"] = category_id

        if is_published is not None:
            filter["is_published"] = is_published

        if search:
            filter["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"title_en": {"$regex": search, "$options": "i"}}
            ]

        return await self.count(filter)

    async def increment_view_count(self, story_id: str) -> bool:
        """增加播放次数"""
        from core.config.database import Database
        from bson import ObjectId
        result = await Database.get_collection(self.collection_name).update_one(
            {"_id": ObjectId(story_id)},
            {"$inc": {"view_count": 1}}
        )
        return result.modified_count > 0

    async def get_random_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取随机故事（用于轮播图）"""
        from core.config.database import Database
        pipeline = [
            {"$match": {"is_published": True}},
            {"$sample": {"size": limit}}
        ]
        cursor = Database.get_collection(self.collection_name).aggregate(pipeline)
        stories = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            stories.append(doc)
        return stories
