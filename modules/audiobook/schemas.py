"""
有声书模块 - Pydantic 模型
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 故事相关 Schema ====================

class AudiobookStoryBase(BaseModel):
    """故事基础字段"""
    title: str = Field(..., min_length=1, max_length=200, description="故事标题（中文）")
    title_en: str = Field(..., min_length=1, max_length=200, description="故事标题（英文）")
    content: str = Field(..., min_length=1, description="故事全文内容")
    language: str = Field(default="en", description="语言: en | zh")
    category: str = Field(default="fairy_tale", description="分类: fairy_tale | fable | adventure | bedtime")
    age_group: str = Field(default="5-8", description="年龄段: 3-5 | 5-8 | 8-12")
    estimated_duration: int = Field(default=0, ge=0, description="预估时长（秒）")
    thumbnail_url: Optional[str] = Field(default=None, description="封面图 URL")
    background_music_url: Optional[str] = Field(default=None, description="背景音乐 URL")


class CreateAudiobookStoryRequest(AudiobookStoryBase):
    """创建故事请求"""
    is_published: bool = Field(default=True, description="是否发布")
    sort_order: int = Field(default=0, description="排序顺序")


class UpdateAudiobookStoryRequest(BaseModel):
    """更新故事请求"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    title_en: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    language: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    age_group: Optional[str] = Field(default=None)
    estimated_duration: Optional[int] = Field(default=None, ge=0)
    thumbnail_url: Optional[str] = Field(default=None)
    background_music_url: Optional[str] = Field(default=None)
    is_published: Optional[bool] = Field(default=None)
    sort_order: Optional[int] = Field(default=None)


class AudiobookStoryResponse(AudiobookStoryBase):
    """故事响应"""
    id: str = Field(..., description="故事 ID")
    is_published: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AudiobookStoryListResponse(BaseModel):
    """故事列表响应"""
    items: List[AudiobookStoryResponse]
    total: int
    page: int
    page_size: int


# ==================== 任务相关 Schema ====================

class CreateAudiobookJobRequest(BaseModel):
    """创建有声书生成任务请求"""
    story_id: str = Field(..., description="故事 ID")
    voice_profile_id: str = Field(..., description="声音档案 ID")


class AudiobookJobResponse(BaseModel):
    """任务响应"""
    id: str = Field(..., description="任务 ID")
    user_id: str
    story_id: str
    voice_profile_id: str
    status: str = Field(..., description="状态: pending | processing | completed | failed")
    progress: int = Field(..., ge=0, le=100, description="进度 0-100")
    current_step: str = Field(..., description="当前步骤: init | tts | mixing | completed")
    audio_url: Optional[str] = Field(default=None, description="生成的音频 URL")
    duration: int = Field(default=0, description="音频时长（秒）")
    story_title: str = Field(default="", description="故事标题")
    voice_name: str = Field(default="", description="声音名称")
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class AudiobookJobListResponse(BaseModel):
    """任务列表响应"""
    items: List[AudiobookJobResponse]
    total: int
    page: int
    page_size: int


# ==================== 管理端任务响应（含用户信息） ====================

class AdminAudiobookJobResponse(AudiobookJobResponse):
    """管理端任务响应（包含用户信息）"""
    user_email: Optional[str] = None
    user_nickname: Optional[str] = None


class AdminAudiobookJobListResponse(BaseModel):
    """管理端任务列表响应"""
    items: List[AdminAudiobookJobResponse]
    total: int
    page: int
    page_size: int
