"""
故事生成模块 - 数据模型定义
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class StoryJobStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StoryJobStep(str, Enum):
    """处理步骤"""
    INIT = "init"
    EXTRACTING_AUDIO = "extracting_audio"           # 提取音频
    SEPARATING_VOCALS = "separating_vocals"         # 分离人声
    TRANSCRIBING = "transcribing"                   # 语音识别
    GENERATING_VOICE = "generating_voice"           # 生成克隆语音
    GENERATING_DIGITAL_HUMAN = "generating_digital_human"  # 生成数字人
    COMPOSITING_VIDEO = "compositing_video"         # 合成视频
    COMPLETED = "completed"


# =============== 请求模型 ===============

class CreateStoryJobRequest(BaseModel):
    """创建故事生成任务请求"""
    story_id: str = Field(..., description="故事 ID")
    voice_profile_id: str = Field(..., description="声音档案 ID")
    avatar_profile_id: str = Field(..., description="头像档案 ID")
    replace_all_voice: bool = Field(default=True, description="是否替换全部人声")
    full_video: bool = Field(default=False, description="是否生成完整视频，默认只生成前2个片段")


class UpdateSubtitleSelectionRequest(BaseModel):
    """更新字幕选择（选择要扮演的角色）"""
    selected_indices: List[int] = Field(..., description="选中的字幕序号列表")


# =============== 响应模型 ===============

class SubtitleItem(BaseModel):
    """字幕项"""
    index: int = Field(..., description="字幕序号")
    start_time: float = Field(..., description="开始时间 (秒)")
    end_time: float = Field(..., description="结束时间 (秒)")
    text: str = Field(..., description="字幕文本")
    speaker: Optional[str] = Field(None, description="说话人标签")
    is_selected: bool = Field(default=True, description="是否选中")


class StoryJobResponse(BaseModel):
    """故事生成任务响应"""
    job_id: str
    story_id: str
    status: StoryJobStatus
    progress: int = Field(default=0, description="进度 0-100")
    current_step: StoryJobStep

    # 输入信息
    voice_profile_id: str
    avatar_profile_id: str

    # 中间产物 URL
    original_audio_url: Optional[str] = None
    vocals_url: Optional[str] = None
    instrumental_url: Optional[str] = None
    subtitle_srt_url: Optional[str] = None
    cloned_audio_url: Optional[str] = None
    digital_human_video_url: Optional[str] = None

    # 输出
    final_video_url: Optional[str] = None

    # 时间
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    # 错误信息
    error: Optional[str] = None


class StoryJobListResponse(BaseModel):
    """任务列表响应"""
    items: List[StoryJobResponse]
    total: int
    page: int
    page_size: int


class SubtitleListResponse(BaseModel):
    """字幕列表响应"""
    subtitles: List[SubtitleItem]
    total_duration: float = Field(..., description="总时长 (秒)")


# =============== APICore 响应模型 ===============

class SunoUploadResponse(BaseModel):
    """Suno 上传音频响应"""
    clip_id: str
    task_id: Optional[str] = None


class SunoStemsResponse(BaseModel):
    """Suno 人声分离响应"""
    vocals: str = Field(..., description="人声 URL")
    instrumental: str = Field(..., description="背景音乐 URL")


class SunoTimingWord(BaseModel):
    """词级时间戳"""
    word: str
    start_s: float
    end_s: float


class SunoTimingResponse(BaseModel):
    """Suno 时间对齐响应"""
    words: List[SunoTimingWord]
