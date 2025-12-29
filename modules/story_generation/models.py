"""
故事生成模块 - MongoDB 文档模型
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId


class StoryJobDocument:
    """故事生成任务文档结构"""

    COLLECTION_NAME = "story_jobs"

    @staticmethod
    def create(
        user_id: str,
        story_id: str,
        voice_profile_id: str,
        avatar_profile_id: str,
        original_video_url: str,
        replace_all_voice: bool = True
    ) -> dict:
        """创建新任务文档"""
        now = datetime.utcnow()
        return {
            "_id": ObjectId(),
            "user_id": ObjectId(user_id),
            "story_id": ObjectId(story_id),
            "voice_profile_id": ObjectId(voice_profile_id),
            # avatar_profile_id 可以为空（暂不使用数字人）
            "avatar_profile_id": ObjectId(avatar_profile_id) if avatar_profile_id and avatar_profile_id.strip() else None,

            # 状态
            "status": "pending",
            "progress": 0,
            "current_step": "init",

            # 输入
            "original_video_url": original_video_url,
            "replace_all_voice": replace_all_voice,

            # 中间产物
            "muted_video_url": None,           # 静音视频
            "original_audio_url": None,        # 原始音频
            "vocals_url": None,                # 人声音轨
            "instrumental_url": None,          # 背景音乐
            "subtitle_srt_url": None,          # SRT 字幕文件
            "subtitle_srt_content": None,      # SRT 字幕内容
            "cloned_audio_url": None,          # 克隆语音
            "digital_human_video_url": None,   # 数字人视频

            # 输出
            "final_video_url": None,           # 最终成片

            # 时间
            "created_at": now,
            "updated_at": now,
            "completed_at": None,

            # 错误信息
            "error": None
        }


class SubtitleDocument:
    """字幕文档结构"""

    COLLECTION_NAME = "story_subtitles"

    @staticmethod
    def create(
        job_id: str,
        index: int,
        start_time: float,
        end_time: float,
        text: str,
        speaker: Optional[str] = None
    ) -> dict:
        """创建字幕文档"""
        return {
            "_id": ObjectId(),
            "job_id": ObjectId(job_id),
            "index": index,
            "start_time": start_time,
            "end_time": end_time,
            "text": text,
            "speaker": speaker,
            "is_selected": True,
            "created_at": datetime.utcnow()
        }

    @staticmethod
    def create_batch(job_id: str, subtitles: List[dict]) -> List[dict]:
        """批量创建字幕文档"""
        docs = []
        for i, sub in enumerate(subtitles):
            docs.append(SubtitleDocument.create(
                job_id=job_id,
                index=i + 1,
                start_time=sub["start_time"],
                end_time=sub["end_time"],
                text=sub["text"],
                speaker=sub.get("speaker")
            ))
        return docs
