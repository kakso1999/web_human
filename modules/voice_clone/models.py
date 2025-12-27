"""
Voice Clone Models - MongoDB 文档模型
用户声音档案管理
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VoiceProfile(BaseModel):
    """用户声音档案"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str                          # 用户ID
    name: str                             # 声音名称（如：爸爸的声音、妈妈的声音）
    voice_id: str                         # 阿里云音色ID
    reference_audio_url: str              # 参考音频URL（图床）
    reference_audio_local: str            # 参考音频本地路径
    preview_audio_url: Optional[str] = None  # 预览音频URL
    status: str = "active"                # 状态：active, deleted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class VoiceProfileCreate(BaseModel):
    """创建声音档案请求"""
    name: str = Field(..., min_length=1, max_length=50, description="声音名称")


class VoiceProfileResponse(BaseModel):
    """声音档案响应"""
    id: str
    name: str
    voice_id: str
    reference_audio_url: str
    preview_audio_url: Optional[str] = None
    created_at: datetime
