"""
有声书模块 - MongoDB 文档模型
"""

from datetime import datetime
from typing import Optional, Dict, Any


def create_audiobook_story_document(
    title: str,
    title_en: str,
    content: str,
    language: str = "en",
    category: str = "fairy_tale",
    age_group: str = "5-8",
    estimated_duration: int = 0,
    thumbnail_url: Optional[str] = None,
    background_music_url: Optional[str] = None,
    is_published: bool = True,
    sort_order: int = 0
) -> Dict[str, Any]:
    """
    创建有声书故事文档

    Args:
        title: 故事标题（中文）
        title_en: 故事标题（英文）
        content: 故事全文内容
        language: 语言 "en" | "zh"
        category: 分类 "fairy_tale" | "fable" | "adventure" | "bedtime"
        age_group: 年龄段 "3-5" | "5-8" | "8-12"
        estimated_duration: 预估时长（秒）
        thumbnail_url: 封面图 URL
        background_music_url: 背景音乐 URL
        is_published: 是否发布
        sort_order: 排序顺序
    """
    return {
        "title": title,
        "title_en": title_en,
        "content": content,
        "language": language,
        "category": category,
        "age_group": age_group,
        "estimated_duration": estimated_duration,
        "thumbnail_url": thumbnail_url,
        "background_music_url": background_music_url,
        "is_published": is_published,
        "sort_order": sort_order,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def create_audiobook_job_document(
    user_id: str,
    story_id: str,
    voice_profile_id: str,
    story_title: str = "",
    voice_name: str = ""
) -> Dict[str, Any]:
    """
    创建有声书生成任务文档

    Args:
        user_id: 用户 ID
        story_id: 故事 ID
        voice_profile_id: 声音档案 ID
        story_title: 故事标题（缓存）
        voice_name: 声音名称（缓存）
    """
    return {
        "user_id": user_id,
        "story_id": story_id,
        "voice_profile_id": voice_profile_id,
        "status": "pending",  # pending | processing | completed | failed
        "progress": 0,
        "current_step": "init",  # init | tts | mixing | completed
        "audio_url": None,
        "duration": 0,
        "story_title": story_title,
        "voice_name": voice_name,
        "created_at": datetime.utcnow(),
        "completed_at": None,
        "error": None
    }


# 故事分类
AUDIOBOOK_CATEGORIES = {
    "fairy_tale": "童话故事",
    "fable": "寓言故事",
    "adventure": "冒险故事",
    "bedtime": "睡前故事"
}

# 年龄段
AGE_GROUPS = {
    "3-5": "3-5岁",
    "5-8": "5-8岁",
    "8-12": "8-12岁"
}

# 任务状态
JOB_STATUS = {
    "pending": "等待中",
    "processing": "生成中",
    "completed": "已完成",
    "failed": "失败"
}

# 任务步骤
JOB_STEPS = {
    "init": "初始化",
    "tts": "语音合成",
    "mixing": "音频混合",
    "completed": "完成"
}
