"""
有声书模块 - API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from core.schemas.base import success_response
from core.middleware.auth import get_current_user_id

from .schemas import (
    CreateAudiobookJobRequest,
    AudiobookStoryResponse,
    AudiobookStoryListResponse,
    AudiobookJobResponse,
    AudiobookJobListResponse
)
from .service import get_audiobook_service

router = APIRouter(prefix="/audiobook", tags=["Audiobook"])


# ==================== 故事 API ====================

@router.get("/stories")
async def list_stories(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    language: Optional[str] = Query(None, description="语言过滤: en | zh"),
    category: Optional[str] = Query(None, description="分类过滤"),
    age_group: Optional[str] = Query(None, description="年龄段过滤"),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取有声书故事列表

    只返回已发布的故事，支持按语言、分类、年龄段筛选。
    """
    service = get_audiobook_service()
    result = await service.list_stories(
        page=page,
        page_size=page_size,
        language=language,
        category=category,
        age_group=age_group,
        published_only=True
    )

    return success_response({
        "items": [
            AudiobookStoryResponse(**story).model_dump()
            for story in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    })


@router.get("/stories/{story_id}")
async def get_story(
    story_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取故事详情

    返回故事的完整内容。
    """
    service = get_audiobook_service()
    story = await service.get_story(story_id)

    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    if not story.get("is_published"):
        raise HTTPException(status_code=404, detail="故事未发布")

    return success_response(
        AudiobookStoryResponse(**story).model_dump()
    )


# ==================== 任务 API ====================

@router.post("/jobs")
async def create_job(
    request: CreateAudiobookJobRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建有声书生成任务

    选择故事和声音档案，后台生成克隆语音版本的有声书。
    返回任务ID，前端轮询 GET /jobs/{job_id} 获取状态。

    - **story_id**: 故事ID
    - **voice_profile_id**: 声音档案ID
    """
    service = get_audiobook_service()

    try:
        result = await service.create_job(
            user_id=user_id,
            story_id=request.story_id,
            voice_profile_id=request.voice_profile_id
        )
        return success_response(result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs")
async def list_jobs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取用户的有声书生成任务列表

    返回当前用户的所有任务，按创建时间倒序。
    """
    service = get_audiobook_service()
    result = await service.list_jobs(
        user_id=user_id,
        page=page,
        page_size=page_size
    )

    return success_response({
        "items": [
            AudiobookJobResponse(**job).model_dump()
            for job in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    })


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取任务详情

    轮询此接口获取任务进度和结果。

    返回:
    - status: pending | processing | completed | failed
    - progress: 0-100 进度百分比
    - audio_url: 完成后的音频URL (completed 状态时返回)
    - error: 错误信息 (failed 状态时返回)
    """
    service = get_audiobook_service()
    job = await service.get_job(user_id, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(
        AudiobookJobResponse(**job).model_dump()
    )
