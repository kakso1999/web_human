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
    UpdateAvatarProfileRequest
)
from .service import digital_human_service, digital_human_tasks

router = APIRouter(prefix="/digital-human", tags=["Digital Human"])


@router.post("/preview")
async def create_digital_human_preview(
    image: UploadFile = File(..., description="头像照片 (清晰正面人像, JPG/PNG)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    创建数字人预览任务

    上传一张清晰的正面人像照片，后台生成动态数字人预览视频。
    返回任务ID，前端轮询 GET /preview/{task_id} 获取状态。

    - **image**: 头像照片 (清晰正面人像, JPG/PNG格式)

    图片要求:
    - 格式: jpg, jpeg, png, bmp, webp
    - 分辨率: 建议 512x512 以上
    - 内容: 清晰正面人像，五官完整，背景简洁
    """

    # 验证图片文件类型
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format. Supported: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )

    # 验证文件大小 (最大 10MB)
    max_size = 10 * 1024 * 1024
    content = await image.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="Image file too large, max 10MB")

    # 保存图片
    image_path = digital_human_service.save_image(
        user_id=user_id,
        file_content=content,
        filename=image.filename or "avatar.jpg"
    )

    # 创建任务
    task_id = digital_human_service.create_task(user_id)
    digital_human_tasks[task_id]["image_local"] = image_path

    # 启动后台任务
    asyncio.create_task(
        digital_human_service.generate_preview(
            task_id=task_id,
            image_path=image_path
        )
    )

    return success_response({
        "task_id": task_id,
        "status": TaskStatus.PROCESSING,
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
