"""
有声书模块 - 数据访问层
"""

from datetime import datetime
from typing import List, Optional, Tuple
from bson import ObjectId

from core.database.mongodb import get_database
from .models import create_audiobook_story_document, create_audiobook_job_document


class AudiobookStoryRepository:
    """有声书故事数据访问"""

    def __init__(self):
        self.collection_name = "audiobook_stories"

    @property
    def collection(self):
        db = get_database()
        return db[self.collection_name]

    async def create(self, story_data: dict) -> str:
        """创建故事"""
        doc = create_audiobook_story_document(**story_data)
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_id(self, story_id: str) -> Optional[dict]:
        """根据ID获取故事"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(story_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        except Exception:
            return None

    async def list_published(
        self,
        page: int = 1,
        page_size: int = 20,
        language: Optional[str] = None,
        category: Optional[str] = None,
        age_group: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """获取已发布的故事列表（用户端）"""
        query = {"is_published": True}

        if language:
            query["language"] = language
        if category:
            query["category"] = category
        if age_group:
            query["age_group"] = age_group

        # 计算总数
        total = await self.collection.count_documents(query)

        # 分页查询
        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort([
            ("sort_order", 1),
            ("created_at", -1)
        ]).skip(skip).limit(page_size)

        stories = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            stories.append(doc)

        return stories, total

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        language: Optional[str] = None,
        category: Optional[str] = None,
        is_published: Optional[bool] = None
    ) -> Tuple[List[dict], int]:
        """获取所有故事列表（管理端）"""
        query = {}

        if language:
            query["language"] = language
        if category:
            query["category"] = category
        if is_published is not None:
            query["is_published"] = is_published

        total = await self.collection.count_documents(query)

        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort([
            ("sort_order", 1),
            ("created_at", -1)
        ]).skip(skip).limit(page_size)

        stories = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            stories.append(doc)

        return stories, total

    async def update(self, story_id: str, update_data: dict) -> bool:
        """更新故事"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(story_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete(self, story_id: str) -> bool:
        """删除故事"""
        result = await self.collection.delete_one({"_id": ObjectId(story_id)})
        return result.deleted_count > 0

    async def count_all(self) -> int:
        """统计故事总数"""
        return await self.collection.count_documents({})


class AudiobookJobRepository:
    """有声书生成任务数据访问"""

    def __init__(self):
        self.collection_name = "audiobook_jobs"

    @property
    def collection(self):
        db = get_database()
        return db[self.collection_name]

    async def create(
        self,
        user_id: str,
        story_id: str,
        voice_profile_id: str,
        story_title: str = "",
        voice_name: str = ""
    ) -> str:
        """创建任务"""
        doc = create_audiobook_job_document(
            user_id=user_id,
            story_id=story_id,
            voice_profile_id=voice_profile_id,
            story_title=story_title,
            voice_name=voice_name
        )
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_id(self, job_id: str) -> Optional[dict]:
        """根据ID获取任务"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(job_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        except Exception:
            return None

    async def get_by_user(self, user_id: str, job_id: str) -> Optional[dict]:
        """获取用户的特定任务"""
        try:
            doc = await self.collection.find_one({
                "_id": ObjectId(job_id),
                "user_id": user_id
            })
            if doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        except Exception:
            return None

    async def list_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取用户的任务列表"""
        query = {"user_id": user_id}

        total = await self.collection.count_documents(query)

        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)

        jobs = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            jobs.append(doc)

        return jobs, total

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """获取所有任务列表（管理端）"""
        query = {}

        if status:
            query["status"] = status
        if user_id:
            query["user_id"] = user_id

        total = await self.collection.count_documents(query)

        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)

        jobs = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            jobs.append(doc)

        return jobs, total

    async def update_status(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        current_step: str = "init",
        error: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        update_data = {
            "status": status,
            "progress": progress,
            "current_step": current_step
        }

        if error:
            update_data["error"] = error

        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def update_field(self, job_id: str, field: str, value) -> bool:
        """更新单个字段"""
        result = await self.collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {field: value}}
        )
        return result.modified_count > 0

    async def update_fields(self, job_id: str, fields: dict) -> bool:
        """更新多个字段"""
        result = await self.collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": fields}
        )
        return result.modified_count > 0

    async def delete(self, job_id: str) -> bool:
        """删除任务"""
        result = await self.collection.delete_one({"_id": ObjectId(job_id)})
        return result.deleted_count > 0

    async def count_by_status(self) -> dict:
        """按状态统计任务数"""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        result = {}
        async for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result


# 全局实例
audiobook_story_repository = AudiobookStoryRepository()
audiobook_job_repository = AudiobookJobRepository()


def get_audiobook_story_repository() -> AudiobookStoryRepository:
    """获取故事仓储"""
    return audiobook_story_repository


def get_audiobook_job_repository() -> AudiobookJobRepository:
    """获取任务仓储"""
    return audiobook_job_repository
