"""
Story 模块 - Schema 定义
故事相关的请求和响应模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SubtitleSegment(BaseModel):
    """字幕片段"""
    start: float  # 开始时间（秒）
    end: float    # 结束时间（秒）
    text: str     # 字幕文本


class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str = Field(..., min_length=1, max_length=50)
    name_en: str = Field(..., min_length=1, max_length=50)
    sort_order: int = Field(default=0, ge=0)


class CategoryCreate(CategoryBase):
    """创建分类请求"""
    pass


class CategoryResponse(CategoryBase):
    """分类响应"""
    id: str
    story_count: int = 0


class StoryBase(BaseModel):
    """故事基础模型"""
    title: str = Field(..., min_length=1, max_length=200)
    title_en: Optional[str] = Field(None, max_length=200)
    category_id: str
    description: Optional[str] = Field(None, max_length=1000)
    description_en: Optional[str] = Field(None, max_length=1000)


class StoryCreate(BaseModel):
    """创建故事请求"""
    title: str = Field(default="", max_length=200)  # 可为空，AI会生成
    title_en: Optional[str] = Field(None, max_length=200)
    category_id: str = ""
    description: Optional[str] = Field(None, max_length=1000)
    description_en: Optional[str] = Field(None, max_length=1000)
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    duration: int = Field(default=0, ge=0)  # 视频时长（秒）
    is_published: bool = False
    is_processing: bool = False  # AI处理中
    subtitles: Optional[List[SubtitleSegment]] = None  # 字幕数据
    subtitle_text: Optional[str] = None  # 完整字幕文本


class StoryUpdate(BaseModel):
    """更新故事请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    title_en: Optional[str] = Field(None, max_length=200)
    category_id: Optional[str] = None
    description: Optional[str] = Field(None, max_length=1000)
    description_en: Optional[str] = Field(None, max_length=1000)
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[int] = Field(None, ge=0)
    is_published: Optional[bool] = None
    subtitles: Optional[List[SubtitleSegment]] = None
    subtitle_text: Optional[str] = None


class StoryResponse(BaseModel):
    """故事响应"""
    id: str
    title: str
    title_en: Optional[str] = None
    category_id: str
    category_name: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    duration: int = 0
    is_published: bool = False
    is_processing: bool = False
    view_count: int = 0
    subtitles: Optional[List[SubtitleSegment]] = None
    subtitle_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StoryListItem(BaseModel):
    """故事列表项"""
    id: str
    title: str
    title_en: Optional[str] = None
    category_id: str
    thumbnail_url: Optional[str] = None
    duration: int = 0
    is_published: bool = False
    is_processing: bool = False
    view_count: int = 0
    created_at: datetime
