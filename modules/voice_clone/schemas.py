"""Voice Clone Schemas - Pydantic Models"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 预设故事相关 ====================

class PresetStoryResponse(BaseModel):
    """预设故事响应"""
    id: str
    title: str
    preview_text: str
    estimated_duration: int


class PresetStoriesListResponse(BaseModel):
    """预设故事列表响应"""
    stories: List[PresetStoryResponse]


# ==================== 声音档案相关 ====================

class SaveVoiceProfileRequest(BaseModel):
    """保存声音档案请求"""
    task_id: str = Field(..., description="语音克隆任务ID")
    name: str = Field(..., min_length=1, max_length=50, description="声音名称，如：爸爸的声音")


class VoiceProfileResponse(BaseModel):
    """声音档案响应"""
    id: str
    name: str
    voice_id: str
    reference_audio_url: str
    preview_audio_url: Optional[str] = None
    created_at: datetime


class VoiceProfileListResponse(BaseModel):
    """声音档案列表响应"""
    profiles: List[VoiceProfileResponse]
    total: int


class UpdateVoiceProfileRequest(BaseModel):
    """更新声音档案请求"""
    name: str = Field(..., min_length=1, max_length=50, description="声音名称")


# ==================== 语音克隆任务相关 ====================

class VoiceCloneTaskCreate(BaseModel):
    """创建语音克隆任务请求（用于文档）"""
    story_id: str  # 预设故事ID
    # audio: File  # 参考音频文件（通过 Form 上传）


class VoiceCloneTaskResponse(BaseModel):
    """语音克隆任务响应"""
    task_id: str
    status: str  # processing, completed, failed
    audio_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class VoiceCloneTaskStatusResponse(BaseModel):
    """语音克隆任务状态响应"""
    task_id: str
    status: str  # processing, completed, failed
    progress: int  # 0-100 进度百分比
    audio_url: Optional[str] = None
    error: Optional[str] = None


# ==================== 内部任务状态 ====================

class TaskStatus:
    """任务状态常量"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
