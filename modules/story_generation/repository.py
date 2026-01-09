"""
故事生成模块 - 数据访问层
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from core.database.mongodb import get_database
from .models import StoryJobDocument, SubtitleDocument
from .schemas import StoryJobStatus, StoryJobStep

import logging

logger = logging.getLogger(__name__)


class StoryGenerationRepository:
    """故事生成任务仓储"""

    def __init__(self):
        self.db = get_database()
        self.jobs_collection = self.db[StoryJobDocument.COLLECTION_NAME]
        self.subtitles_collection = self.db[SubtitleDocument.COLLECTION_NAME]

    # ===================== Job 操作 =====================

    async def create_job(
        self,
        user_id: str,
        story_id: str,
        voice_profile_id: str,
        avatar_profile_id: str,
        original_video_url: str,
        replace_all_voice: bool = True,
        full_video: bool = False
    ) -> str:
        """创建新任务"""
        doc = StoryJobDocument.create(
            user_id=user_id,
            story_id=story_id,
            voice_profile_id=voice_profile_id,
            avatar_profile_id=avatar_profile_id,
            original_video_url=original_video_url,
            replace_all_voice=replace_all_voice,
            full_video=full_video
        )
        result = await self.jobs_collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        try:
            doc = await self.jobs_collection.find_one({"_id": ObjectId(job_id)})
            return self._serialize_job(doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None

    async def get_job_by_user(
        self,
        user_id: str,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取用户的任务"""
        try:
            doc = await self.jobs_collection.find_one({
                "_id": ObjectId(job_id),
                "user_id": ObjectId(user_id)
            })
            return self._serialize_job(doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting job {job_id} for user {user_id}: {e}")
            return None

    async def list_jobs_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取用户的任务列表"""
        skip = (page - 1) * page_size
        query = {"user_id": ObjectId(user_id)}

        cursor = self.jobs_collection.find(query).sort(
            "created_at", -1
        ).skip(skip).limit(page_size)

        jobs = []
        async for doc in cursor:
            jobs.append(self._serialize_job(doc))

        total = await self.jobs_collection.count_documents(query)
        return jobs, total

    async def update_job_status(
        self,
        job_id: str,
        status: StoryJobStatus,
        progress: int = None,
        current_step: StoryJobStep = None,
        error: str = None
    ) -> bool:
        """更新任务状态"""
        update = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }

        if progress is not None:
            update["progress"] = progress

        if current_step is not None:
            update["current_step"] = current_step.value

        if error is not None:
            update["error"] = error

        if status == StoryJobStatus.COMPLETED:
            update["completed_at"] = datetime.utcnow()

        result = await self.jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update}
        )
        return result.modified_count > 0

    async def update_job_field(
        self,
        job_id: str,
        field: str,
        value: Any
    ) -> bool:
        """更新任务字段"""
        result = await self.jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {field: value, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def update_job_fields(
        self,
        job_id: str,
        fields: Dict[str, Any]
    ) -> bool:
        """批量更新任务字段"""
        fields["updated_at"] = datetime.utcnow()
        result = await self.jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": fields}
        )
        return result.modified_count > 0

    # ===================== Subtitle 操作 =====================

    async def save_subtitles(
        self,
        job_id: str,
        subtitles: List[Dict[str, Any]]
    ) -> int:
        """保存字幕列表"""
        # 先删除旧字幕
        await self.subtitles_collection.delete_many({
            "job_id": ObjectId(job_id)
        })

        # 插入新字幕
        docs = SubtitleDocument.create_batch(job_id, subtitles)
        if docs:
            result = await self.subtitles_collection.insert_many(docs)
            return len(result.inserted_ids)
        return 0

    async def get_subtitles(
        self,
        job_id: str,
        only_selected: bool = False
    ) -> List[Dict[str, Any]]:
        """获取字幕列表"""
        query = {"job_id": ObjectId(job_id)}
        if only_selected:
            query["is_selected"] = True

        cursor = self.subtitles_collection.find(query).sort("index", 1)
        subtitles = []
        async for doc in cursor:
            subtitles.append(self._serialize_subtitle(doc))
        return subtitles

    async def update_subtitle_selection(
        self,
        job_id: str,
        selected_indices: List[int]
    ) -> bool:
        """更新字幕选择状态"""
        # 先全部设为未选中
        await self.subtitles_collection.update_many(
            {"job_id": ObjectId(job_id)},
            {"$set": {"is_selected": False}}
        )

        # 设置选中的
        if selected_indices:
            await self.subtitles_collection.update_many(
                {
                    "job_id": ObjectId(job_id),
                    "index": {"$in": selected_indices}
                },
                {"$set": {"is_selected": True}}
            )

        return True

    # ===================== 序列化 =====================

    def _serialize_job(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """序列化任务文档"""
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "user_id": str(doc["user_id"]),
            "story_id": str(doc["story_id"]),
            "voice_profile_id": str(doc["voice_profile_id"]),
            "avatar_profile_id": str(doc["avatar_profile_id"]) if doc.get("avatar_profile_id") else None,
            "status": doc["status"],
            "progress": doc["progress"],
            "current_step": doc["current_step"],
            "original_video_url": doc.get("original_video_url"),
            "muted_video_url": doc.get("muted_video_url"),
            "original_audio_url": doc.get("original_audio_url"),
            "vocals_url": doc.get("vocals_url"),
            "instrumental_url": doc.get("instrumental_url"),
            "subtitle_srt_url": doc.get("subtitle_srt_url"),
            "subtitle_srt_content": doc.get("subtitle_srt_content"),
            "cloned_audio_url": doc.get("cloned_audio_url"),
            "digital_human_video_url": doc.get("digital_human_video_url"),
            "final_video_url": doc.get("final_video_url"),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
            "completed_at": doc.get("completed_at"),
            "error": doc.get("error"),
            "replace_all_voice": doc.get("replace_all_voice", True),
            "full_video": doc.get("full_video", False)
        }

    def _serialize_subtitle(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """序列化字幕文档"""
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "job_id": str(doc["job_id"]),
            "index": doc["index"],
            "start_time": doc["start_time"],
            "end_time": doc["end_time"],
            "text": doc["text"],
            "speaker": doc.get("speaker"),
            "is_selected": doc.get("is_selected", True)
        }


# 单例
_repository: Optional[StoryGenerationRepository] = None


def get_story_generation_repository() -> StoryGenerationRepository:
    """获取仓储单例"""
    global _repository
    if _repository is None:
        _repository = StoryGenerationRepository()
    return _repository
