"""
Digital Human Models - MongoDB 文档模型
用户数字人头像档案管理
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AvatarProfile(BaseModel):
    """用户数字人头像档案"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str                              # 用户ID
    name: str                                 # 头像名称（如：爸爸的头像、妈妈的头像）
    image_url: str                            # 原始图片URL（图床）
    image_local: str                          # 原始图片本地路径
    face_bbox: List[int]                      # 人脸区域坐标 [x1, y1, x2, y2]
    ext_bbox: List[int]                       # 动态区域坐标 [x1, y1, x2, y2]
    preview_video_url: Optional[str] = None   # 预览视频URL
    status: str = "active"                    # 状态：active, deleted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class AvatarProfileCreate(BaseModel):
    """创建头像档案请求"""
    name: str = Field(..., min_length=1, max_length=50, description="头像名称")


class AvatarProfileResponse(BaseModel):
    """头像档案响应"""
    id: str
    name: str
    image_url: str
    preview_video_url: Optional[str] = None
    created_at: datetime
