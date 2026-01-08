"""
Audiobook 模块 - API 路由
有声书相关接口，用户选择故事和声音生成个性化有声书
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

router = APIRouter(prefix="/audiobook", tags=["有声书"])


# ==================== 故事 API ====================

@router.get("/stories", summary="获取有声书故事列表")
async def list_stories(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    language: Optional[str] = Query(None, description="语言筛选：en(英语) | zh(中文)"),
    category: Optional[str] = Query(None, description="分类筛选：fairy_tale | fable | adventure | bedtime"),
    age_group: Optional[str] = Query(None, description="年龄段筛选：3-5 | 5-8 | 8-12"),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取有声书故事列表

    返回平台上所有可用的有声书故事模板。
    支持按语言、分类、年龄段进行筛选。

    **请求参数:**
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，1-100
    - **language**: 语言筛选（可选）
    - **category**: 分类筛选（可选）
    - **age_group**: 年龄段筛选（可选）

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": "695342ec383483bf26139d89",
                    "title": "三只小猪",
                    "title_en": "The Three Little Pigs",
                    "content": "Once upon a time...",
                    "language": "en",
                    "category": "fairy_tale",
                    "age_group": "5-8",
                    "estimated_duration": 180,
                    "thumbnail_url": "/uploads/audiobook/cover.jpg",
                    "is_published": true
                }
            ],
            "total": 10,
            "page": 1,
            "page_size": 20
        }
    }
    ```
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


@router.get("/stories/{story_id}", summary="获取有声书故事详情")
async def get_story(
    story_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取有声书故事详情

    返回故事的完整内容，包括用于 TTS 合成的文本。

    **路径参数:**
    - **story_id**: 故事唯一标识ID

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "695342ec383483bf26139d89",
            "title": "三只小猪",
            "title_en": "The Three Little Pigs",
            "content": "Once upon a time, there were three little pigs who lived with their mother...",
            "language": "en",
            "category": "fairy_tale",
            "age_group": "5-8",
            "estimated_duration": 180,
            "thumbnail_url": "/uploads/audiobook/cover.jpg",
            "background_music_url": "/uploads/audiobook/bgm.mp3",
            "is_published": true,
            "created_at": "2025-01-01T12:00:00",
            "updated_at": "2025-01-01T12:00:00"
        }
    }
    ```
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

@router.post("/jobs", summary="创建有声书生成任务")
async def create_job(
    request: CreateAudiobookJobRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建有声书生成任务

    选择一个故事和一个声音档案，系统会使用该声音朗读故事内容，生成个性化有声书。
    这是一个异步任务，创建后需要轮询 GET /jobs/{job_id} 获取结果。

    **请求参数:**
    - **story_id**: 有声书故事ID（从故事列表获取）
    - **voice_profile_id**: 声音档案ID（从语音克隆模块获取）

    **处理流程:**
    1. 验证故事和声音档案存在
    2. 使用 CosyVoice TTS 合成语音
    3. （可选）与背景音乐混合
    4. 上传最终音频文件

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "695345efc32ffbd6151c18a9",
            "user_id": "6948bda91fd873cf81f5addd",
            "story_id": "695342ec383483bf26139d89",
            "voice_profile_id": "694534f1c32ffbd6151c18a3",
            "status": "pending",
            "progress": 0,
            "current_step": "init",
            "story_title": "三只小猪",
            "voice_name": "爸爸的声音",
            "created_at": "2025-01-01T12:00:00"
        }
    }
    ```
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


@router.get("/jobs", summary="获取有声书任务列表")
async def list_jobs(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取用户的有声书生成任务列表

    返回当前用户创建的所有有声书任务，按创建时间倒序排列。
    可用于展示"我的有声书"页面。

    **请求参数:**
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，1-100

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": "695345efc32ffbd6151c18a9",
                    "status": "completed",
                    "progress": 100,
                    "audio_url": "/uploads/audiobook/user123/output.mp3",
                    "duration": 185,
                    "story_title": "三只小猪",
                    "voice_name": "爸爸的声音",
                    "created_at": "2025-01-01T12:00:00",
                    "completed_at": "2025-01-01T12:03:00"
                }
            ],
            "total": 5,
            "page": 1,
            "page_size": 20
        }
    }
    ```
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


@router.get("/jobs/{job_id}", summary="获取有声书任务状态")
async def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取有声书任务状态

    轮询此接口获取任务的处理进度和结果。
    建议轮询间隔：2-3秒。

    **路径参数:**
    - **job_id**: 任务ID（从 POST /jobs 返回）

    **任务状态说明:**
    - **pending**: 等待处理
    - **processing**: 处理中
    - **completed**: 完成，audio_url 包含生成的音频
    - **failed**: 失败，error 包含错误信息

    **处理步骤说明:**
    - **init**: 初始化任务
    - **tts**: 语音合成中
    - **mixing**: 音频混合中（添加背景音乐）
    - **completed**: 处理完成

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "695345efc32ffbd6151c18a9",
            "user_id": "6948bda91fd873cf81f5addd",
            "story_id": "695342ec383483bf26139d89",
            "voice_profile_id": "694534f1c32ffbd6151c18a3",
            "status": "completed",
            "progress": 100,
            "current_step": "completed",
            "audio_url": "/uploads/audiobook/user123/output.mp3",
            "duration": 185,
            "story_title": "三只小猪",
            "voice_name": "爸爸的声音",
            "created_at": "2025-01-01T12:00:00",
            "completed_at": "2025-01-01T12:03:00",
            "error": null
        }
    }
    ```
    """
    service = get_audiobook_service()
    job = await service.get_job(user_id, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(
        AudiobookJobResponse(**job).model_dump()
    )
