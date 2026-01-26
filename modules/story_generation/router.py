"""
故事生成模块 - API 路由
"""
import logging
import traceback
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional

from core.middleware.auth import get_current_user_id
from .service import get_story_generation_service
from .schemas import (
    CreateStoryJobRequest,
    UpdateSubtitleSelectionRequest,
    StoryJobResponse,
    StoryJobListResponse,
    SubtitleListResponse,
    AnalyzeStoryResponse,
    SpeakersResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/story_generation", tags=["story-generation"])


# ==================== 说话人分析 ====================

@router.post("/analyze/{story_id}", summary="分析故事说话人")
async def analyze_story_speakers(
    story_id: str,
    background_tasks: BackgroundTasks,
    num_speakers: Optional[int] = None,
    user_id: str = Depends(get_current_user_id)
):
    """
    触发故事音频的说话人分析

    分析流程：
    1. 从视频提取音频
    2. 使用 Demucs 分离人声/背景音
    3. 使用 Pyannote 进行说话人分割
    4. 提取各说话人独立音轨
    5. 更新故事的说话人信息

    参数：
    - story_id: 故事 ID
    - num_speakers: 预设说话人数量 (可选，不填则自动检测)

    返回：
    - 分析结果或已在后台开始分析的消息
    """
    service = get_story_generation_service()

    try:
        # 检查故事是否存在
        from modules.story.repository import StoryRepository
        story_repo = StoryRepository()
        story = await story_repo.get_by_id(story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )

        # 检查是否已分析
        if story.get("is_analyzed"):
            return {
                "code": 0,
                "message": "Story already analyzed",
                "data": {
                    "story_id": story_id,
                    "speaker_count": story.get("speaker_count", 0),
                    "speakers": story.get("speakers", []),
                    "is_analyzed": True
                }
            }

        # 获取视频路径
        video_url = story.get("video_url")
        if not video_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Story has no video"
            )

        # 转换为本地路径
        from core.config.settings import get_settings
        from pathlib import Path
        import os
        settings = get_settings()

        if video_url.startswith("/"):
            # video_url 格式: /uploads/videos/xxx.mp4
            # 需要使用项目根目录拼接，而不是 UPLOAD_DIR
            project_root = Path(__file__).parent.parent.parent
            video_path = str(project_root / video_url.lstrip("/"))
        elif video_url.startswith("http"):
            # 远程视频需要先下载
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Remote video analysis not supported yet"
            )
        else:
            video_path = video_url

        # 后台执行分析
        background_tasks.add_task(
            service.analyze_story_audio_task,
            story_id,
            video_path,
            num_speakers
        )

        return {
            "code": 0,
            "message": "Analysis started in background",
            "data": {
                "story_id": story_id,
                "status": "analyzing"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/speakers/{story_id}", summary="获取故事说话人信息")
async def get_story_speakers(
    story_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取故事的说话人信息

    返回：
    - speaker_count: 说话人数量
    - speakers: 说话人列表 (含音轨 URL、时长等)
    - background_audio_url: 背景音 URL
    - is_analyzed: 是否已完成分析
    """
    from modules.story.repository import StoryRepository
    story_repo = StoryRepository()
    story = await story_repo.get_by_id(story_id)

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "story_id": story_id,
            "speaker_count": story.get("speaker_count", 0),
            "speakers": story.get("speakers", []),
            "background_audio_url": story.get("background_audio_url"),
            "diarization_segments": story.get("diarization_segments", []),
            "is_analyzed": story.get("is_analyzed", False),
            "analysis_error": story.get("analysis_error"),
            # 新架构：两种分析模式
            "single_speaker_analysis": story.get("single_speaker_analysis"),
            "dual_speaker_analysis": story.get("dual_speaker_analysis")
        }
    }


@router.post("/subtitles/{story_id}", summary="生成说话人字幕")
async def generate_speaker_subtitles(
    story_id: str,
    background_tasks: BackgroundTasks,
    force: bool = False,
    user_id: str = Depends(get_current_user_id)
):
    """
    为故事的所有说话人生成词级字幕

    注意：此端点已废弃。在新架构中，字幕在故事上传时通过 APIMart API 自动生成。
    此端点现在仅返回已存在的字幕。

    前提：故事必须已完成分析（is_analyzed=True）
    """
    from modules.story.repository import StoryRepository

    story_repo = StoryRepository()
    story = await story_repo.get_by_id(story_id)

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )

    if not story.get("is_analyzed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story not analyzed yet. Subtitles are generated automatically during story upload."
        )

    # 获取已存在的字幕
    existing_subtitles = story.get("subtitles")

    if not existing_subtitles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subtitles available. Story analysis may not have completed successfully."
        )

    # 新架构使用列表格式，兼容旧格式的字典
    if isinstance(existing_subtitles, list):
        # 新格式：直接返回列表
        return {
            "code": 0,
            "message": "Subtitles retrieved from analysis",
            "data": {
                "story_id": story_id,
                "subtitles": existing_subtitles,
                "has_subtitles": True
            }
        }
    elif isinstance(existing_subtitles, dict):
        # 旧格式：字典格式
        return {
            "code": 0,
            "message": "Subtitles retrieved (legacy format)",
            "data": {
                "story_id": story_id,
                "subtitles": existing_subtitles,
                "has_subtitles": True
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid subtitles format"
        )


@router.get("/subtitles/{story_id}", summary="获取故事字幕")
async def get_story_subtitles(
    story_id: str,
    speaker_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取故事的词级字幕

    参数：
    - story_id: 故事 ID
    - speaker_id: 说话人 ID (可选，不填返回所有)

    返回：
    - 指定说话人的字幕，或全部字幕
    """
    from modules.story.repository import StoryRepository

    story_repo = StoryRepository()
    story = await story_repo.get_by_id(story_id)

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )

    subtitles = story.get("subtitles")
    if not subtitles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subtitles found. Please generate subtitles first."
        )

    if speaker_id:
        if speaker_id not in subtitles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Speaker {speaker_id} not found"
            )
        return {
            "code": 0,
            "message": "success",
            "data": {
                "story_id": story_id,
                "speaker_id": speaker_id,
                "subtitles": subtitles[speaker_id]
            }
        }

    return {
        "code": 0,
        "message": "success",
        "data": {
            "story_id": story_id,
            "subtitles": subtitles
        }
    }


@router.post("/jobs", summary="创建故事生成任务")
async def create_job(
    request: CreateStoryJobRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建故事生成任务

    支持两种模式：
    1. 单说话人模式：使用 voice_profile_id 和 avatar_profile_id
    2. 多说话人模式：使用 speaker_configs 数组，为每个说话人配置声音和头像

    流程：
    1. 提取视频音频
    2. 分离人声/背景音
    3. 语音识别生成字幕
    4. 为每个说话人生成克隆语音
    5. 为每个说话人生成数字人视频
    6. 合成最终视频（多数字人画中画）

    参数：
    - full_video: 默认 False 只生成前2个片段预览，设为 True 生成完整视频
    - speaker_configs: 多说话人配置（优先使用）
    """
    logger.info(f"create_job called: user_id={user_id}, story_id={request.story_id}, mode={request.mode}, full_video={request.full_video}")
    logger.info(f"  speaker_configs: {request.speaker_configs}")
    service = get_story_generation_service()

    try:
        # 转换 speaker_configs 为字典列表
        speaker_configs = None
        if request.speaker_configs:
            speaker_configs = [cfg.model_dump() for cfg in request.speaker_configs]

        result = await service.create_job(
            user_id=user_id,
            story_id=request.story_id,
            mode=request.mode.value,  # 传递模式: 'single' 或 'dual'
            voice_profile_id=request.voice_profile_id,
            avatar_profile_id=request.avatar_profile_id,
            speaker_configs=speaker_configs,
            replace_all_voice=request.replace_all_voice,
            full_video=request.full_video
        )
        logger.info(f"create_job success: {result}")
        return {
            "code": 0,
            "message": "Job created successfully",
            "data": result
        }
    except ValueError as e:
        logger.error(f"ValueError in create_job: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Exception in create_job: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs", summary="获取任务列表")
async def list_jobs(
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_current_user_id)
):
    """获取用户的故事生成任务列表"""
    service = get_story_generation_service()

    result = await service.list_jobs(user_id, page, page_size)
    return {
        "code": 0,
        "message": "success",
        "data": result
    }


@router.get("/jobs/{job_id}", summary="获取任务详情")
async def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """获取任务详情和进度"""
    service = get_story_generation_service()

    job = await service.get_job(user_id, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return {
        "code": 0,
        "message": "success",
        "data": job
    }


@router.get("/jobs/{job_id}/subtitles", summary="获取字幕列表")
async def get_subtitles(
    job_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """获取任务的字幕列表，用于角色选择"""
    service = get_story_generation_service()

    try:
        result = await service.get_subtitles(user_id, job_id)
        return {
            "code": 0,
            "message": "success",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/jobs/{job_id}/subtitles", summary="更新字幕选择")
async def update_subtitle_selection(
    job_id: str,
    request: UpdateSubtitleSelectionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """更新字幕选择（选择要扮演的角色台词）"""
    service = get_story_generation_service()

    # 验证任务存在
    job = await service.get_job(user_id, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # 更新选择
    repository = service.repository
    await repository.update_subtitle_selection(job_id, request.selected_indices)

    return {
        "code": 0,
        "message": "Subtitle selection updated"
    }


@router.get("/queue/status", summary="获取任务队列状态")
async def get_queue_status(
    user_id: str = Depends(get_current_user_id)
):
    """
    获取故事生成任务队列状态

    返回：
    - queue_size: 队列中等待的任务数
    - current_job: 当前正在处理的任务 ID
    - worker_running: worker 是否在运行
    """
    service = get_story_generation_service()
    queue_status = service.get_queue_status()

    return {
        "code": 0,
        "message": "success",
        "data": queue_status
    }
