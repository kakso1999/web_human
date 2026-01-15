"""
Voice Clone 模块 - Schema 定义
语音克隆相关的请求和响应模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ==================== 预设故事相关 ====================

class PresetStoryResponse(BaseModel):
    """预设故事响应

    用于语音克隆预览的预设故事，包含适合朗读的英文文本。
    """
    id: str = Field(..., description="故事唯一标识ID")
    title: str = Field(..., description="故事标题")
    preview_text: str = Field(..., description="故事文本，约15秒朗读时长")
    estimated_duration: int = Field(..., description="预估朗读时长（秒）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "story_little_star",
                "title": "Twinkle Little Star",
                "preview_text": "Twinkle, twinkle, little star, how I wonder what you are...",
                "estimated_duration": 15
            }
        }
    )


class PresetStoriesListResponse(BaseModel):
    """预设故事列表响应"""
    stories: List[PresetStoryResponse] = Field(..., description="预设故事列表")


# ==================== 声音档案相关 ====================

class SaveVoiceProfileRequest(BaseModel):
    """保存声音档案请求

    语音克隆预览成功后，将克隆的声音保存为档案。
    保存后可在故事生成、有声书等功能中重复使用。
    """
    task_id: str = Field(
        ...,
        description="已完成的语音克隆任务ID",
        json_schema_extra={"example": "user123_1703980800000"}
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="声音名称，便于识别，如：爸爸的声音、妈妈的声音",
        json_schema_extra={"example": "爸爸的声音"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "user123_1703980800000",
                "name": "爸爸的声音"
            }
        }
    )


class VoiceProfileResponse(BaseModel):
    """声音档案响应

    包含声音档案的完整信息，用于展示和管理。
    """
    id: str = Field(..., description="档案唯一标识ID")
    name: str = Field(..., description="声音名称")
    voice_id: str = Field(..., description="阿里云 CosyVoice 声音ID，用于 TTS 调用")
    reference_audio_url: str = Field(default="", description="参考音频文件URL（本地模式可能为空）")
    preview_audio_url: Optional[str] = Field(None, description="预览音频URL（克隆后生成的）")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "694534f1c32ffbd6151c18a3",
                "name": "爸爸的声音",
                "voice_id": "cosyvoice-clone-xxxx",
                "reference_audio_url": "/uploads/voice/user123/ref_audio.wav",
                "preview_audio_url": "/uploads/voice/user123/preview.mp3",
                "created_at": "2025-01-01T12:00:00"
            }
        }
    )


class VoiceProfileListResponse(BaseModel):
    """声音档案列表响应"""
    profiles: List[VoiceProfileResponse] = Field(..., description="声音档案列表")
    total: int = Field(..., description="档案总数")


class UpdateVoiceProfileRequest(BaseModel):
    """更新声音档案请求

    用于修改声音档案的名称。
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="新的声音名称",
        json_schema_extra={"example": "妈妈的声音"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "妈妈的声音"
            }
        }
    )


# ==================== 语音克隆任务相关 ====================

class VoiceCloneTaskCreate(BaseModel):
    """创建语音克隆任务请求

    上传参考音频并选择预设故事，系统会克隆音色并生成预览音频。
    """
    story_id: str = Field(
        ...,
        description="预设故事ID，从 /preset-stories 接口获取",
        json_schema_extra={"example": "story_little_star"}
    )
    # audio: File  # 参考音频文件（通过 Form 上传）


class VoiceCloneTaskResponse(BaseModel):
    """语音克隆任务响应

    创建任务后返回的任务信息。
    """
    task_id: str = Field(..., description="任务唯一标识ID")
    status: str = Field(..., description="任务状态：processing(处理中) / completed(已完成) / failed(失败)")
    audio_url: Optional[str] = Field(None, description="生成的音频URL（完成后返回）")
    error: Optional[str] = Field(None, description="错误信息（失败时返回）")
    created_at: datetime = Field(..., description="任务创建时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "user123_1703980800000",
                "status": "completed",
                "audio_url": "/uploads/voice/user123/preview.mp3",
                "error": None,
                "created_at": "2025-01-01T12:00:00",
                "completed_at": "2025-01-01T12:00:30"
            }
        }
    )


class VoiceCloneTaskStatusResponse(BaseModel):
    """语音克隆任务状态响应

    轮询任务状态时返回的详细信息。
    """
    task_id: str = Field(..., description="任务唯一标识ID")
    status: str = Field(..., description="任务状态：processing(处理中) / completed(已完成) / failed(失败)")
    progress: int = Field(..., ge=0, le=100, description="处理进度百分比，0-100")
    audio_url: Optional[str] = Field(None, description="生成的音频URL（完成后返回）")
    error: Optional[str] = Field(None, description="错误信息（失败时返回）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "user123_1703980800000",
                "status": "processing",
                "progress": 65,
                "audio_url": None,
                "error": None
            }
        }
    )


# ==================== 内部任务状态 ====================

class TaskStatus:
    """任务状态常量"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
