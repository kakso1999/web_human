"""
Voice Clone Router - API Endpoints
语音克隆相关的 API 接口
"""

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from typing import Optional
from datetime import datetime

from core.schemas.base import success_response
from core.middleware.auth import get_current_user_id
from core.config.settings import get_settings

settings = get_settings()

from .schemas import (
    PresetStoryResponse,
    PresetStoriesListResponse,
    VoiceCloneTaskResponse,
    VoiceCloneTaskStatusResponse,
    TaskStatus
)
from .preset_stories import get_all_stories, get_story_by_id
from .service import voice_clone_service, voice_clone_tasks

router = APIRouter(prefix="/voice-clone", tags=["Voice Clone"])


@router.get("/preset-stories")
async def get_preset_stories():
    """
    获取预设故事列表

    返回 5 个预设的英文故事，每个故事约 15 秒朗读时长
    """
    stories = get_all_stories()

    return success_response({
        "stories": [
            PresetStoryResponse(
                id=s["id"],
                title=s["title"],
                title_zh=s["title_zh"],
                preview_text=s["preview_text"],
                estimated_duration=s["estimated_duration"]
            ).model_dump()
            for s in stories
        ]
    })


@router.post("/preview")
async def create_voice_clone_preview(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(..., description="参考音频文件 (10-15秒, WAV/MP3)"),
    story_id: str = Form(..., description="预设故事ID"),
    user_id: str = Depends(get_current_user_id)
):
    """
    创建语音克隆预览任务

    上传参考音频并选择预设故事，后台生成克隆语音预览。
    返回任务ID，前端轮询 GET /preview/{task_id} 获取状态。

    - **audio**: 参考音频文件 (10-15秒清晰语音, WAV/MP3格式)
    - **story_id**: 预设故事ID (从 /preset-stories 获取)
    """

    # 验证故事ID
    story = get_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=400, detail="无效的故事ID")

    # 验证音频文件类型
    if audio.content_type not in settings.ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式。支持的格式: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
        )

    # 验证文件大小 (最大 10MB)
    max_size = 10 * 1024 * 1024
    content = await audio.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="音频文件过大，最大支持 10MB")

    # 保存参考音频
    reference_path = voice_clone_service.save_reference_audio(
        user_id=user_id,
        file_content=content,
        filename=audio.filename or "audio.wav"
    )

    # 创建任务
    task_id = voice_clone_service.create_task(user_id)

    # 后台执行语音克隆
    background_tasks.add_task(
        voice_clone_service.generate_preview,
        task_id=task_id,
        reference_audio_path=reference_path,
        text=story["preview_text"]
    )

    return success_response({
        "task_id": task_id,
        "status": TaskStatus.PROCESSING,
        "message": "语音克隆任务已创建，请轮询获取状态"
    })


@router.get("/preview/{task_id}")
async def get_voice_clone_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取语音克隆任务状态

    轮询此接口获取任务进度和结果。

    - **task_id**: 任务ID (从 POST /preview 返回)

    返回:
    - status: processing / completed / failed
    - progress: 0-100 进度百分比
    - audio_url: 完成后的音频URL (completed 状态时返回)
    - error: 错误信息 (failed 状态时返回)
    """

    # 验证任务ID属于当前用户
    if not task_id.startswith(user_id):
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 获取任务状态
    task = voice_clone_service.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(
        VoiceCloneTaskStatusResponse(
            task_id=task_id,
            status=task["status"],
            progress=task.get("progress", 0),
            audio_url=task.get("audio_url"),
            error=task.get("error")
        ).model_dump()
    )
