"""
Story 模块 - Schema 定义
故事相关的请求和响应模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class SubtitleSegment(BaseModel):
    """字幕片段

    视频中的单条字幕，包含时间信息和文本内容。
    """
    start: float = Field(..., description="开始时间（秒）", json_schema_extra={"example": 0.0})
    end: float = Field(..., description="结束时间（秒）", json_schema_extra={"example": 3.5})
    text: str = Field(..., description="字幕文本", json_schema_extra={"example": "Hello, welcome to the story."})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": 0.0,
                "end": 3.5,
                "text": "Hello, welcome to the story."
            }
        }
    )


class SpeakerInfo(BaseModel):
    """说话人信息

    表示视频中识别出的一个说话人。
    """
    speaker_id: str = Field(..., description="说话人ID", json_schema_extra={"example": "SPEAKER_00"})
    label: str = Field(default="", description="用户可编辑的标签", json_schema_extra={"example": "爸爸"})
    gender: str = Field(default="unknown", description="性别: male/female/unknown", json_schema_extra={"example": "male"})
    audio_url: Optional[str] = Field(None, description="该说话人的独立音轨URL")
    duration: float = Field(default=0.0, description="该说话人总发言时长（秒）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "speaker_id": "SPEAKER_00",
                "label": "爸爸",
                "gender": "male",
                "audio_url": "http://example.com/speaker_00.wav",
                "duration": 120.5
            }
        }
    )


class DiarizationSegment(BaseModel):
    """说话人分割片段

    表示某个时间段内的说话人。
    """
    start: float = Field(..., description="开始时间（秒）")
    end: float = Field(..., description="结束时间（秒）")
    speaker: str = Field(..., description="说话人ID")


class SingleSpeakerAnalysis(BaseModel):
    """单人模式分析结果

    不进行说话人分割，将所有人声作为一个整体处理。
    适用于：用同一个声音和头像替换所有人声。
    """
    vocals_url: Optional[str] = Field(None, description="完整人声音轨URL")
    background_url: Optional[str] = Field(None, description="背景音URL")
    duration: float = Field(default=0.0, description="人声总时长（秒）")
    is_analyzed: bool = Field(default=False, description="是否已完成分析")


class DualSpeakerAnalysis(BaseModel):
    """双人模式分析结果

    进行说话人分割（最多2人），为每个说话人分离独立音轨。
    适用于：为爸爸和妈妈分别配置不同的声音和头像。
    """
    speakers: List[SpeakerInfo] = Field(default=[], description="说话人列表（最多2人）")
    background_url: Optional[str] = Field(None, description="背景音URL")
    diarization_segments: List[DiarizationSegment] = Field(default=[], description="说话人分割片段")
    is_analyzed: bool = Field(default=False, description="是否已完成分析")


class CategoryBase(BaseModel):
    """分类基础模型

    故事分类的基础字段定义。
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分类中文名称",
        json_schema_extra={"example": "童话故事"}
    )
    name_en: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分类英文名称",
        json_schema_extra={"example": "Fairy Tales"}
    )
    sort_order: int = Field(
        default=0,
        ge=0,
        description="排序序号，数字越小越靠前",
        json_schema_extra={"example": 0}
    )


class CategoryCreate(CategoryBase):
    """创建分类请求

    用于管理员创建新的故事分类。
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "童话故事",
                "name_en": "Fairy Tales",
                "sort_order": 0
            }
        }
    )


class CategoryResponse(CategoryBase):
    """分类响应

    返回分类信息，包含故事数量统计。
    """
    id: str = Field(..., description="分类唯一标识ID")
    story_count: int = Field(default=0, description="该分类下的故事数量")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "694534f1c32ffbd6151c18a1",
                "name": "童话故事",
                "name_en": "Fairy Tales",
                "sort_order": 0,
                "story_count": 15
            }
        }
    )


class StoryBase(BaseModel):
    """故事基础模型

    故事的基础字段定义。
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="故事中文标题",
        json_schema_extra={"example": "三只小猪"}
    )
    title_en: Optional[str] = Field(
        None,
        max_length=200,
        description="故事英文标题",
        json_schema_extra={"example": "The Three Little Pigs"}
    )
    category_id: str = Field(..., description="所属分类ID")
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="故事中文简介"
    )
    description_en: Optional[str] = Field(
        None,
        max_length=1000,
        description="故事英文简介"
    )


class StoryCreate(BaseModel):
    """创建故事请求

    用于管理员创建新故事。上传视频后系统会自动：
    1. 从视频第10秒提取缩略图
    2. 获取视频时长
    3. 提取音频并生成字幕
    4. 使用 AI 生成标题（如未提供）
    5. 进行说话人分析和人声分离
    """
    title: str = Field(
        default="",
        max_length=200,
        description="故事标题，可为空由AI生成"
    )
    title_en: Optional[str] = Field(None, max_length=200, description="英文标题")
    category_id: str = Field(default="", description="分类ID")
    description: Optional[str] = Field(None, max_length=1000, description="故事简介")
    description_en: Optional[str] = Field(None, max_length=1000, description="英文简介")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    video_url: Optional[str] = Field(None, description="视频URL")
    audio_url: Optional[str] = Field(None, description="音频URL")
    duration: int = Field(default=0, ge=0, description="视频时长（秒）")
    is_published: bool = Field(default=False, description="是否发布")
    is_processing: bool = Field(default=False, description="是否处理中")
    subtitles: Optional[List[SubtitleSegment]] = Field(None, description="字幕数据")
    subtitle_text: Optional[str] = Field(None, description="完整字幕文本")
    # 说话人分析相关字段 (旧字段，保持向后兼容)
    speaker_count: int = Field(default=0, description="说话人数量")
    speakers: Optional[List[SpeakerInfo]] = Field(None, description="说话人列表")
    background_audio_url: Optional[str] = Field(None, description="背景音/环境音URL")
    diarization_segments: Optional[List[DiarizationSegment]] = Field(None, description="说话人分割片段")
    is_analyzed: bool = Field(default=False, description="是否已完成说话人分析")
    analysis_error: Optional[str] = Field(None, description="分析失败原因")

    # 新架构：单人/双人两种分析模式
    single_speaker_analysis: Optional[SingleSpeakerAnalysis] = Field(
        None, description="单人模式分析结果（人声整体 + 背景音）"
    )
    dual_speaker_analysis: Optional[DualSpeakerAnalysis] = Field(
        None, description="双人模式分析结果（说话人1 + 说话人2 + 背景音）"
    )


class StoryUpdate(BaseModel):
    """更新故事请求

    用于管理员更新故事信息，所有字段可选。
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="故事标题")
    title_en: Optional[str] = Field(None, max_length=200, description="英文标题")
    category_id: Optional[str] = Field(None, description="分类ID")
    description: Optional[str] = Field(None, max_length=1000, description="故事简介")
    description_en: Optional[str] = Field(None, max_length=1000, description="英文简介")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    video_url: Optional[str] = Field(None, description="视频URL")
    audio_url: Optional[str] = Field(None, description="音频URL")
    duration: Optional[int] = Field(None, ge=0, description="视频时长（秒）")
    is_published: Optional[bool] = Field(None, description="是否发布")
    subtitles: Optional[List[SubtitleSegment]] = Field(None, description="字幕数据")
    subtitle_text: Optional[str] = Field(None, description="完整字幕文本")
    # 说话人分析相关字段 (旧字段，保持向后兼容)
    speaker_count: Optional[int] = Field(None, description="说话人数量")
    speakers: Optional[List[SpeakerInfo]] = Field(None, description="说话人列表")
    background_audio_url: Optional[str] = Field(None, description="背景音/环境音URL")
    diarization_segments: Optional[List[DiarizationSegment]] = Field(None, description="说话人分割片段")
    is_analyzed: Optional[bool] = Field(None, description="是否已完成说话人分析")
    analysis_error: Optional[str] = Field(None, description="分析失败原因")

    # 新架构：单人/双人两种分析模式
    single_speaker_analysis: Optional[SingleSpeakerAnalysis] = Field(
        None, description="单人模式分析结果（人声整体 + 背景音）"
    )
    dual_speaker_analysis: Optional[DualSpeakerAnalysis] = Field(
        None, description="双人模式分析结果（说话人1 + 说话人2 + 背景音）"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "三只小猪",
                "title_en": "The Three Little Pigs",
                "is_published": True
            }
        }
    )


class StoryResponse(BaseModel):
    """故事详情响应

    返回故事的完整信息，包含字幕等详情。
    """
    id: str = Field(..., description="故事唯一标识ID")
    title: str = Field(..., description="故事标题")
    title_en: Optional[str] = Field(None, description="英文标题")
    category_id: str = Field(..., description="分类ID")
    category_name: Optional[str] = Field(None, description="分类名称")
    description: Optional[str] = Field(None, description="故事简介")
    description_en: Optional[str] = Field(None, description="英文简介")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    video_url: Optional[str] = Field(None, description="视频URL")
    audio_url: Optional[str] = Field(None, description="音频URL")
    duration: int = Field(default=0, description="视频时长（秒）")
    is_published: bool = Field(default=False, description="是否已发布")
    is_processing: bool = Field(default=False, description="是否处理中")
    view_count: int = Field(default=0, description="播放次数")
    subtitles: Optional[List[SubtitleSegment]] = Field(None, description="字幕数据列表")
    subtitle_text: Optional[str] = Field(None, description="完整字幕文本")
    # 说话人分析相关字段 (旧字段，保持向后兼容)
    speaker_count: int = Field(default=0, description="说话人数量")
    speakers: Optional[List[SpeakerInfo]] = Field(None, description="说话人列表")
    background_audio_url: Optional[str] = Field(None, description="背景音/环境音URL")
    is_analyzed: bool = Field(default=False, description="是否已完成说话人分析")
    analysis_error: Optional[str] = Field(None, description="分析失败原因")
    # 新架构：单人/双人两种分析模式
    single_speaker_analysis: Optional[SingleSpeakerAnalysis] = Field(
        None, description="单人模式分析结果（人声整体 + 背景音）"
    )
    dual_speaker_analysis: Optional[DualSpeakerAnalysis] = Field(
        None, description="双人模式分析结果（说话人1 + 说话人2 + 背景音）"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "694534f1c32ffbd6151c18a2",
                "title": "三只小猪",
                "title_en": "The Three Little Pigs",
                "category_id": "694534f1c32ffbd6151c18a1",
                "category_name": "童话故事",
                "description": "三只小猪建房子的经典童话故事",
                "thumbnail_url": "/uploads/thumbnails/story123.jpg",
                "video_url": "/uploads/videos/story123.mp4",
                "duration": 180,
                "is_published": True,
                "is_processing": False,
                "view_count": 1234,
                "speaker_count": 2,
                "is_analyzed": True,
                "created_at": "2025-01-01T12:00:00",
                "updated_at": "2025-01-01T12:00:00"
            }
        }
    )


class StoryListItem(BaseModel):
    """故事列表项

    用于列表展示的简化故事信息。
    """
    id: str = Field(..., description="故事唯一标识ID")
    title: str = Field(..., description="故事标题")
    title_en: Optional[str] = Field(None, description="英文标题")
    category_id: Optional[str] = Field(None, description="分类ID")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    duration: int = Field(default=0, description="视频时长（秒）")
    is_published: bool = Field(default=False, description="是否已发布")
    is_processing: bool = Field(default=False, description="是否处理中")
    view_count: int = Field(default=0, description="播放次数")
    # 说话人分析状态 (旧字段，保持向后兼容)
    speaker_count: int = Field(default=0, description="说话人数量")
    is_analyzed: bool = Field(default=False, description="是否已完成说话人分析")
    # 新架构：分析状态
    single_speaker_ready: bool = Field(default=False, description="单人模式是否已就绪")
    dual_speaker_ready: bool = Field(default=False, description="双人模式是否已就绪")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "694534f1c32ffbd6151c18a2",
                "title": "三只小猪",
                "title_en": "The Three Little Pigs",
                "category_id": "694534f1c32ffbd6151c18a1",
                "thumbnail_url": "/uploads/thumbnails/story123.jpg",
                "duration": 180,
                "is_published": True,
                "is_processing": False,
                "view_count": 1234,
                "speaker_count": 2,
                "is_analyzed": True,
                "created_at": "2025-01-01T12:00:00"
            }
        }
    )
