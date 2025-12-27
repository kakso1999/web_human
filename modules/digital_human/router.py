"""
Digital Human Router - API Endpoints
数字人头像相关的 API 接口
"""

import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional

from core.schemas.base import success_response
from core.middleware.auth import get_current_user_id
from core.config.settings import get_settings

settings = get_settings()

from .schemas import (
    DigitalHumanTaskStatusResponse,
    TaskStatus,
    SaveAvatarProfileRequest,
    AvatarProfileResponse,
    UpdateAvatarProfileRequest,
    AudioSourceType
)
from .service import digital_human_service, digital_human_tasks

router = APIRouter(prefix="/digital-human", tags=["Digital Human"])


@router.post("/preview")
async def create_digital_human_preview(
    image: UploadFile = File(..., description="头像照片 (清晰正面人像, JPG/PNG)"),
    audio: Optional[UploadFile] = File(None, description="音频文件 (可选，用于数字人说话)"),
    voice_profile_id: Optional[str] = Form(None, description="已保存的声音档案ID (可选)"),
    preview_text: Optional[str] = Form(None, description="预览文本，使用声音档案时需要提供"),
    user_id: str = Depends(get_current_user_id)
):
    """
    创建数字人预览任务

    上传一张清晰的正面人像照片，后台生成动态数字人预览视频。
    返回任务ID，前端轮询 GET /preview/{task_id} 获取状态。

    音频来源（三选一）:
    1. 不传音频参数 - 使用系统默认音色生成预览
    2. 上传 audio 文件 - 直接使用上传的音频
    3. 传 voice_profile_id + preview_text - 使用已保存的克隆声音合成音频

    - **image**: 头像照片 (清晰正面人像, JPG/PNG格式)
    - **audio**: 音频文件 (可选, WAV/MP3格式)
    - **voice_profile_id**: 声音档案ID (可选)
    - **preview_text**: 预览文本 (使用声音档案时需要)
    """

    # 验证图片文件类型
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format. Supported: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )

    # 验证文件大小 (最大 10MB)
    max_size = 10 * 1024 * 1024
    image_content = await image.read()
    if len(image_content) > max_size:
        raise HTTPException(status_code=400, detail="Image file too large, max 10MB")

    # 确定音频来源
    audio_source = AudioSourceType.DEFAULT
    audio_path = None
    audio_content = None

    if audio is not None:
        # 上传了音频文件
        if audio.content_type not in settings.ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
            )
        audio_content = await audio.read()
        if len(audio_content) > 20 * 1024 * 1024:  # 20MB
            raise HTTPException(status_code=400, detail="Audio file too large, max 20MB")
        audio_source = AudioSourceType.UPLOAD

    elif voice_profile_id:
        # 使用声音档案
        if not preview_text:
            raise HTTPException(
                status_code=400,
                detail="preview_text is required when using voice_profile_id"
            )
        audio_source = AudioSourceType.VOICE_PROFILE

    # 保存图片
    image_path = digital_human_service.save_image(
        user_id=user_id,
        file_content=image_content,
        filename=image.filename or "avatar.jpg"
    )

    # 保存音频（如果上传了）
    if audio_content:
        audio_path = digital_human_service.save_audio(
            user_id=user_id,
            file_content=audio_content,
            filename=audio.filename or "audio.wav"
        )

    # 创建任务
    task_id = digital_human_service.create_task(user_id)
    digital_human_tasks[task_id]["image_local"] = image_path
    digital_human_tasks[task_id]["audio_source"] = audio_source.value

    # 启动后台任务
    asyncio.create_task(
        digital_human_service.generate_preview(
            task_id=task_id,
            image_path=image_path,
            audio_source=audio_source,
            audio_path=audio_path,
            voice_profile_id=voice_profile_id,
            preview_text=preview_text or "Hello, I am your digital avatar. Nice to meet you!"
        )
    )

    return success_response({
        "task_id": task_id,
        "status": TaskStatus.PROCESSING,
        "audio_source": audio_source.value,
        "message": "Digital human task created, poll for status"
    })


@router.get("/preview/{task_id}")
async def get_digital_human_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取数字人任务状态

    轮询此接口获取任务进度和结果。

    - **task_id**: 任务ID (从 POST /preview 返回)

    返回:
    - status: detecting / generating / completed / failed
    - progress: 0-100 进度百分比
    - video_url: 完成后的视频URL (completed 状态时返回)
    - error: 错误信息 (failed 状态时返回)
    """

    # 验证任务ID属于当前用户
    if not task_id.startswith(user_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # 获取任务状态
    task = digital_human_service.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return success_response(
        DigitalHumanTaskStatusResponse(
            task_id=task_id,
            status=task["status"],
            progress=task.get("progress", 0),
            video_url=task.get("video_url"),
            error=task.get("error")
        ).model_dump()
    )


# ==================== 头像档案管理 ====================

@router.post("/profiles")
async def save_avatar_profile(
    request: SaveAvatarProfileRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    保存头像档案

    在数字人预览完成后，保存该头像到用户的头像库中。

    - **task_id**: 已完成的数字人任务ID
    - **name**: 头像名称（如：爸爸的头像、妈妈的头像）
    """
    profile = await digital_human_service.save_avatar_profile(
        user_id=user_id,
        task_id=request.task_id,
        name=request.name
    )

    if not profile:
        raise HTTPException(status_code=400, detail="Cannot save avatar profile, ensure task is completed")

    return success_response({
        "profile": AvatarProfileResponse(
            id=profile["id"],
            name=profile["name"],
            image_url=profile["image_url"],
            preview_video_url=profile.get("preview_video_url"),
            created_at=profile["created_at"]
        ).model_dump()
    })


@router.get("/profiles")
async def get_avatar_profiles(
    user_id: str = Depends(get_current_user_id)
):
    """
    获取用户的所有头像档案

    返回用户保存的所有头像档案列表。
    """
    profiles = await digital_human_service.get_user_avatar_profiles(user_id)

    return success_response({
        "profiles": [
            AvatarProfileResponse(
                id=p["_id"],
                name=p["name"],
                image_url=p["image_url"],
                preview_video_url=p.get("preview_video_url"),
                created_at=p["created_at"]
            ).model_dump()
            for p in profiles
        ],
        "total": len(profiles)
    })


@router.get("/profiles/{profile_id}")
async def get_avatar_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """获取单个头像档案详情"""
    profile = await digital_human_service.get_avatar_profile(profile_id, user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Avatar profile not found")

    return success_response(
        AvatarProfileResponse(
            id=profile["_id"],
            name=profile["name"],
            image_url=profile["image_url"],
            preview_video_url=profile.get("preview_video_url"),
            created_at=profile["created_at"]
        ).model_dump()
    )


@router.put("/profiles/{profile_id}")
async def update_avatar_profile(
    profile_id: str,
    request: UpdateAvatarProfileRequest,
    user_id: str = Depends(get_current_user_id)
):
    """更新头像档案名称"""
    success = await digital_human_service.update_avatar_profile(
        profile_id=profile_id,
        user_id=user_id,
        name=request.name
    )

    if not success:
        raise HTTPException(status_code=404, detail="Avatar profile not found or access denied")

    return success_response({"message": "Updated successfully"})


@router.delete("/profiles/{profile_id}")
async def delete_avatar_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """删除头像档案"""
    success = await digital_human_service.delete_avatar_profile(profile_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Avatar profile not found or access denied")

    return success_response({"message": "Deleted successfully"})
