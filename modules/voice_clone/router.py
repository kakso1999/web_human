"""
Voice Clone Router - API Endpoints
语音克隆相关的 API 接口
"""

import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
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
    TaskStatus,
    SaveVoiceProfileRequest,
    VoiceProfileResponse,
    UpdateVoiceProfileRequest
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
                preview_text=s["preview_text"],
                estimated_duration=s["estimated_duration"]
            ).model_dump()
            for s in stories
        ]
    })


@router.post("/preview")
async def create_voice_clone_preview(
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

    # 使用 asyncio.create_task 在独立协程中执行（而非 BackgroundTasks）
    # 这样可以避免 BackgroundTasks 的一些潜在问题
    asyncio.create_task(
        voice_clone_service.generate_preview(
            task_id=task_id,
            reference_audio_path=reference_path,
            text=story["preview_text"]
        )
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


# ==================== 声音档案管理 ====================

@router.post("/profiles")
async def save_voice_profile(
    request: SaveVoiceProfileRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    保存声音档案

    在语音克隆预览完成后，保存该声音到用户的声音库中。

    - **task_id**: 已完成的语音克隆任务ID
    - **name**: 声音名称（如：爸爸的声音、妈妈的声音）
    """
    profile = await voice_clone_service.save_voice_profile(
        user_id=user_id,
        task_id=request.task_id,
        name=request.name
    )

    if not profile:
        raise HTTPException(status_code=400, detail="无法保存声音档案，请确保任务已完成")

    return success_response({
        "profile": VoiceProfileResponse(
            id=profile["id"],
            name=profile["name"],
            voice_id=profile["voice_id"],
            reference_audio_url=profile["reference_audio_url"],
            preview_audio_url=profile.get("preview_audio_url"),
            created_at=profile["created_at"]
        ).model_dump()
    })


@router.get("/profiles")
async def get_voice_profiles(
    user_id: str = Depends(get_current_user_id)
):
    """
    获取用户的所有声音档案

    返回用户保存的所有声音档案列表。
    """
    profiles = await voice_clone_service.get_user_voice_profiles(user_id)

    return success_response({
        "profiles": [
            VoiceProfileResponse(
                id=p["_id"],
                name=p["name"],
                voice_id=p["voice_id"],
                reference_audio_url=p["reference_audio_url"],
                preview_audio_url=p.get("preview_audio_url"),
                created_at=p["created_at"]
            ).model_dump()
            for p in profiles
        ],
        "total": len(profiles)
    })


@router.get("/profiles/{profile_id}")
async def get_voice_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """获取单个声音档案详情"""
    profile = await voice_clone_service.get_voice_profile(profile_id, user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="声音档案不存在")

    return success_response(
        VoiceProfileResponse(
            id=profile["_id"],
            name=profile["name"],
            voice_id=profile["voice_id"],
            reference_audio_url=profile["reference_audio_url"],
            preview_audio_url=profile.get("preview_audio_url"),
            created_at=profile["created_at"]
        ).model_dump()
    )


@router.put("/profiles/{profile_id}")
async def update_voice_profile(
    profile_id: str,
    request: UpdateVoiceProfileRequest,
    user_id: str = Depends(get_current_user_id)
):
    """更新声音档案名称"""
    success = await voice_clone_service.update_voice_profile(
        profile_id=profile_id,
        user_id=user_id,
        name=request.name
    )

    if not success:
        raise HTTPException(status_code=404, detail="声音档案不存在或无权修改")

    return success_response({"message": "更新成功"})


@router.delete("/profiles/{profile_id}")
async def delete_voice_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """删除声音档案"""
    success = await voice_clone_service.delete_voice_profile(profile_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="声音档案不存在或无权删除")

    return success_response({"message": "删除成功"})
