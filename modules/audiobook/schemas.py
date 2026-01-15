"""
Audiobook 模块 - Schema 定义
有声书相关的请求和响应模型
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==================== 故事相关 Schema ====================

class AudiobookStoryBase(BaseModel):
    """有声书故事基础字段

    用于管理端创建和更新故事的基础字段定义。
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="故事标题（中文）",
        json_schema_extra={"example": "三只小猪"}
    )
    title_en: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="故事标题（英文）",
        json_schema_extra={"example": "The Three Little Pigs"}
    )
    content: str = Field(
        ...,
        min_length=1,
        description="故事全文内容，将用于 TTS 生成语音",
        json_schema_extra={"example": "Once upon a time, there were three little pigs..."}
    )
    language: str = Field(
        default="en",
        description="语言代码：en(英语) | zh(中文)",
        json_schema_extra={"example": "en"}
    )
    category: str = Field(
        default="fairy_tale",
        description="分类：fairy_tale(童话) | fable(寓言) | adventure(冒险) | bedtime(睡前故事)",
        json_schema_extra={"example": "fairy_tale"}
    )
    age_group: str = Field(
        default="5-8",
        description="适合年龄段：3-5 | 5-8 | 8-12",
        json_schema_extra={"example": "5-8"}
    )
    estimated_duration: int = Field(
        default=0,
        ge=0,
        description="预估朗读时长（秒）",
        json_schema_extra={"example": 180}
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="封面图URL",
        json_schema_extra={"example": "/uploads/audiobook/story123/cover.jpg"}
    )
    background_music_url: Optional[str] = Field(
        default=None,
        description="背景音乐URL（可选）",
        json_schema_extra={"example": "/uploads/audiobook/story123/bgm.mp3"}
    )


class CreateAudiobookStoryRequest(AudiobookStoryBase):
    """创建有声书故事请求

    管理员创建新的有声书故事模板。
    """
    is_published: bool = Field(
        default=True,
        description="是否发布",
        json_schema_extra={"example": True}
    )
    sort_order: int = Field(
        default=0,
        description="排序序号，数字越小越靠前",
        json_schema_extra={"example": 0}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "三只小猪",
                "title_en": "The Three Little Pigs",
                "content": "Once upon a time, there were three little pigs...",
                "language": "en",
                "category": "fairy_tale",
                "age_group": "5-8",
                "estimated_duration": 180,
                "is_published": True,
                "sort_order": 0
            }
        }
    )


class UpdateAudiobookStoryRequest(BaseModel):
    """更新有声书故事请求

    管理员更新故事信息，所有字段可选。
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="故事标题（中文）")
    title_en: Optional[str] = Field(default=None, min_length=1, max_length=200, description="故事标题（英文）")
    content: Optional[str] = Field(default=None, min_length=1, description="故事全文内容")
    language: Optional[str] = Field(default=None, description="语言代码")
    category: Optional[str] = Field(default=None, description="分类")
    age_group: Optional[str] = Field(default=None, description="适合年龄段")
    estimated_duration: Optional[int] = Field(default=None, ge=0, description="预估时长（秒）")
    thumbnail_url: Optional[str] = Field(default=None, description="封面图URL")
    background_music_url: Optional[str] = Field(default=None, description="背景音乐URL")
    is_published: Optional[bool] = Field(default=None, description="是否发布")
    sort_order: Optional[int] = Field(default=None, description="排序序号")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "三只小猪（更新版）",
                "is_published": True
            }
        }
    )


class AudiobookStoryResponse(AudiobookStoryBase):
    """有声书故事响应

    返回故事的完整信息。
    """
    id: str = Field(..., description="故事唯一标识ID")
    is_published: bool = Field(..., description="是否已发布")
    sort_order: int = Field(..., description="排序序号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "695342ec383483bf26139d89",
                "title": "三只小猪",
                "title_en": "The Three Little Pigs",
                "content": "Once upon a time, there were three little pigs...",
                "language": "en",
                "category": "fairy_tale",
                "age_group": "5-8",
                "estimated_duration": 180,
                "thumbnail_url": "/uploads/audiobook/story123/cover.jpg",
                "background_music_url": None,
                "is_published": True,
                "sort_order": 0,
                "created_at": "2025-01-01T12:00:00",
                "updated_at": "2025-01-01T12:00:00"
            }
        }
    )


class AudiobookStoryListResponse(BaseModel):
    """有声书故事列表响应"""
    items: List[AudiobookStoryResponse] = Field(..., description="故事列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


# ==================== 任务相关 Schema ====================

class CreateAudiobookJobRequest(BaseModel):
    """创建有声书生成任务请求

    用户选择故事和声音档案，创建有声书生成任务。
    """
    story_id: str = Field(
        ...,
        description="有声书故事ID",
        json_schema_extra={"example": "695342ec383483bf26139d89"}
    )
    voice_profile_id: str = Field(
        ...,
        description="声音档案ID，从语音克隆模块获取",
        json_schema_extra={"example": "694534f1c32ffbd6151c18a3"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "story_id": "695342ec383483bf26139d89",
                "voice_profile_id": "694534f1c32ffbd6151c18a3"
            }
        }
    )


class AudiobookJobResponse(BaseModel):
    """有声书任务响应

    返回任务的完整状态和结果信息。
    """
    id: str = Field(..., description="任务唯一标识ID")
    user_id: str = Field(..., description="用户ID")
    story_id: str = Field(..., description="故事ID")
    voice_profile_id: str = Field(..., description="声音档案ID")
    status: str = Field(
        ...,
        description="任务状态：pending(等待) | processing(处理中) | completed(完成) | failed(失败)"
    )
    progress: int = Field(
        ...,
        ge=0,
        le=100,
        description="处理进度百分比，0-100"
    )
    current_step: str = Field(
        ...,
        description="当前处理步骤：init(初始化) | tts(语音合成) | mixing(音频混合) | completed(完成)"
    )
    audio_url: Optional[str] = Field(
        default=None,
        description="生成的音频文件URL（完成后返回）"
    )
    duration: int = Field(
        default=0,
        description="音频时长（秒）"
    )
    story_title: str = Field(
        default="",
        description="故事标题（缓存，便于展示）"
    )
    voice_name: str = Field(
        default="",
        description="声音名称（缓存，便于展示）"
    )
    created_at: datetime = Field(..., description="任务创建时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    error: Optional[str] = Field(None, description="错误信息（失败时返回）")
    is_favorite: bool = Field(default=False, description="是否收藏")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "695345efc32ffbd6151c18a9",
                "user_id": "6948bda91fd873cf81f5addd",
                "story_id": "695342ec383483bf26139d89",
                "voice_profile_id": "694534f1c32ffbd6151c18a3",
                "status": "completed",
                "progress": 100,
                "current_step": "completed",
                "audio_url": "/uploads/audiobook/user123/job456/output.mp3",
                "duration": 185,
                "story_title": "三只小猪",
                "voice_name": "爸爸的声音",
                "created_at": "2025-01-01T12:00:00",
                "completed_at": "2025-01-01T12:03:00",
                "error": None
            }
        }
    )


class AudiobookJobListResponse(BaseModel):
    """有声书任务列表响应"""
    items: List[AudiobookJobResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


# ==================== 管理端任务响应（含用户信息） ====================

class AdminAudiobookJobResponse(AudiobookJobResponse):
    """管理端有声书任务响应

    在用户端响应基础上，额外包含用户信息。
    """
    user_email: Optional[str] = Field(None, description="用户邮箱")
    user_nickname: Optional[str] = Field(None, description="用户昵称")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "695345efc32ffbd6151c18a9",
                "user_id": "6948bda91fd873cf81f5addd",
                "user_email": "user@example.com",
                "user_nickname": "小明",
                "story_id": "695342ec383483bf26139d89",
                "voice_profile_id": "694534f1c32ffbd6151c18a3",
                "status": "completed",
                "progress": 100,
                "current_step": "completed",
                "audio_url": "/uploads/audiobook/user123/job456/output.mp3",
                "duration": 185,
                "story_title": "三只小猪",
                "voice_name": "爸爸的声音",
                "created_at": "2025-01-01T12:00:00",
                "completed_at": "2025-01-01T12:03:00",
                "error": None
            }
        }
    )


class AdminAudiobookJobListResponse(BaseModel):
    """管理端有声书任务列表响应"""
    items: List[AdminAudiobookJobResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


# ==================== 用户电子书 Schema ====================

class EbookMetadata(BaseModel):
    """电子书元数据"""
    word_count: int = Field(default=0, description="词数")
    char_count: int = Field(default=0, description="字符数")
    estimated_duration: int = Field(default=0, description="预估时长（秒）")


class CreateUserEbookRequest(BaseModel):
    """创建用户电子书请求（直接上传文本内容）"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="电子书标题",
        json_schema_extra={"example": "我的故事"}
    )
    content: str = Field(
        ...,
        min_length=1,
        description="电子书文本内容",
        json_schema_extra={"example": "从前有座山，山上有座庙..."}
    )
    language: str = Field(
        default="zh",
        description="语言代码：en(英语) | zh(中文)",
        json_schema_extra={"example": "zh"}
    )


class UpdateUserEbookRequest(BaseModel):
    """更新用户电子书请求"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="电子书标题")
    content: Optional[str] = Field(default=None, min_length=1, description="电子书内容")
    language: Optional[str] = Field(default=None, description="语言代码")


class UserEbookResponse(BaseModel):
    """用户电子书响应"""
    id: str = Field(..., description="电子书唯一标识ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="电子书标题")
    content: str = Field(..., description="电子书文本内容")
    language: str = Field(..., description="语言代码")
    source_format: str = Field(default="txt", description="来源格式")
    source_file_url: Optional[str] = Field(default=None, description="原始文件URL")
    thumbnail_url: Optional[str] = Field(default=None, description="封面图URL")
    metadata: EbookMetadata = Field(..., description="元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "696342ec383483bf26139d89",
                "user_id": "6948bda91fd873cf81f5addd",
                "title": "我的故事",
                "content": "从前有座山...",
                "language": "zh",
                "source_format": "txt",
                "metadata": {
                    "word_count": 100,
                    "char_count": 500,
                    "estimated_duration": 167
                },
                "created_at": "2025-01-15T12:00:00",
                "updated_at": "2025-01-15T12:00:00"
            }
        }
    )


class UserEbookListResponse(BaseModel):
    """用户电子书列表响应"""
    items: List[UserEbookResponse] = Field(..., description="电子书列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class CreateEbookJobRequest(BaseModel):
    """从用户电子书创建有声书任务请求"""
    ebook_id: str = Field(
        ...,
        description="用户电子书ID",
        json_schema_extra={"example": "696342ec383483bf26139d89"}
    )
    voice_profile_id: str = Field(
        ...,
        description="声音档案ID",
        json_schema_extra={"example": "694534f1c32ffbd6151c18a3"}
    )
