"""
Digital Human 模块 - Schema 定义
数字人头像相关的请求和响应模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class AudioSourceType(str, Enum):
    """音频来源类型

    用于指定数字人预览任务的音频来源。
    """
    DEFAULT = "default"           # 使用系统默认音色
    VOICE_PROFILE = "voice_profile"  # 使用已保存的声音档案
    UPLOAD = "upload"             # 直接上传音频文件


# ==================== 数字人头像档案相关 ====================

class SaveAvatarProfileRequest(BaseModel):
    """保存头像档案请求

    数字人预览成功后，将头像保存为档案。
    保存后可在故事生成功能中重复使用。
    """
    task_id: str = Field(
        ...,
        description="已完成的数字人预览任务ID",
        json_schema_extra={"example": "user123_1703980800000"}
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="头像名称，便于识别，如：爸爸的头像、妈妈的头像",
        json_schema_extra={"example": "爸爸的头像"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "user123_1703980800000",
                "name": "爸爸的头像"
            }
        }
    )


class AvatarProfileResponse(BaseModel):
    """头像档案响应

    包含头像档案的完整信息，用于展示和管理。
    """
    id: str = Field(..., description="档案唯一标识ID")
    name: str = Field(..., description="头像名称")
    image_url: str = Field(default="", description="头像图片URL（本地模式可能为空）")
    preview_video_url: Optional[str] = Field(None, description="预览视频URL（数字人动态效果）")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "694534f1c32ffbd6151c18a4",
                "name": "爸爸的头像",
                "image_url": "/uploads/avatar/user123/photo.jpg",
                "preview_video_url": "/uploads/avatar/user123/preview.mp4",
                "created_at": "2025-01-01T12:00:00"
            }
        }
    )


class AvatarProfileListResponse(BaseModel):
    """头像档案列表响应"""
    profiles: List[AvatarProfileResponse] = Field(..., description="头像档案列表")
    total: int = Field(..., description="档案总数")


class UpdateAvatarProfileRequest(BaseModel):
    """更新头像档案请求

    用于修改头像档案的名称。
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="新的头像名称",
        json_schema_extra={"example": "妈妈的头像"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "妈妈的头像"
            }
        }
    )


# ==================== 数字人预览任务相关 ====================

class DigitalHumanTaskStatusResponse(BaseModel):
    """数字人任务状态响应

    轮询任务状态时返回的详细信息。
    """
    task_id: str = Field(..., description="任务唯一标识ID")
    status: str = Field(
        ...,
        description="任务状态：detecting(图像检测中) / generating(视频生成中) / completed(已完成) / failed(失败)"
    )
    progress: int = Field(..., ge=0, le=100, description="处理进度百分比，0-100")
    video_url: Optional[str] = Field(None, description="生成的视频URL（完成后返回）")
    error: Optional[str] = Field(None, description="错误信息（失败时返回）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "user123_1703980800000",
                "status": "generating",
                "progress": 65,
                "video_url": None,
                "error": None
            }
        }
    )


class TaskStatus:
    """任务状态常量"""
    PENDING = "pending"
    DETECTING = "detecting"      # 图像检测中
    GENERATING = "generating"    # 视频生成中
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
