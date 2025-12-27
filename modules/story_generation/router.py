"""
故事生成模块 - API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from core.middleware.auth import get_current_user_id
from .service import get_story_generation_service
from .schemas import (
    CreateStoryJobRequest,
    UpdateSubtitleSelectionRequest,
    StoryJobResponse,
    StoryJobListResponse,
    SubtitleListResponse
)

router = APIRouter(prefix="/story-generation", tags=["story-generation"])


@router.post("/jobs", summary="创建故事生成任务")
async def create_job(
    request: CreateStoryJobRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建故事生成任务

    流程：
    1. 提取视频音频
    2. 分离人声/背景音
    3. 语音识别生成字幕
    4. 生成克隆语音
    5. 生成数字人视频
    6. 合成最终视频
    """
    service = get_story_generation_service()

    try:
        result = await service.create_job(
            user_id=user_id,
            story_id=request.story_id,
            voice_profile_id=request.voice_profile_id,
            avatar_profile_id=request.avatar_profile_id,
            replace_all_voice=request.replace_all_voice
        )
        return {
            "code": 0,
            "message": "Job created successfully",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
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
