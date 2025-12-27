"""Digital Human Schemas - Pydantic Models"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 数字人头像档案相关 ====================

class SaveAvatarProfileRequest(BaseModel):
    """保存头像档案请求"""
    task_id: str = Field(..., description="数字人预览任务ID")
    name: str = Field(..., min_length=1, max_length=50, description="头像名称，如：爸爸的头像")


class AvatarProfileResponse(BaseModel):
    """头像档案响应"""
    id: str
    name: str
    image_url: str
    preview_video_url: Optional[str] = None
    created_at: datetime


class AvatarProfileListResponse(BaseModel):
    """头像档案列表响应"""
    profiles: List[AvatarProfileResponse]
    total: int


class UpdateAvatarProfileRequest(BaseModel):
    """更新头像档案请求"""
    name: str = Field(..., min_length=1, max_length=50, description="头像名称")


# ==================== 数字人预览任务相关 ====================

class DigitalHumanTaskStatusResponse(BaseModel):
    """数字人任务状态响应"""
    task_id: str
    status: str  # processing, completed, failed
    progress: int  # 0-100 进度百分比
    video_url: Optional[str] = None
    error: Optional[str] = None


class TaskStatus:
    """任务状态常量"""
    PENDING = "pending"
    DETECTING = "detecting"      # 图像检测中
    GENERATING = "generating"    # 视频生成中
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
