"""
Digital Human 模块 - API 路由
数字人头像相关接口，支持照片生成动态数字人和头像档案管理
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
from .factory import get_digital_human_service


def _get_service():
    """获取数字人服务实例"""
    return get_digital_human_service()

router = APIRouter(prefix="/digital-human", tags=["数字人"])


@router.post("/preview", summary="创建数字人预览任务")
async def create_digital_human_preview(
    image: UploadFile = File(..., description="头像照片，清晰正面人像，JPG/PNG格式"),
    audio: Optional[UploadFile] = File(None, description="音频文件（可选），用于数字人说话"),
    voice_profile_id: Optional[str] = Form(None, description="已保存的声音档案ID（可选）"),
    preview_text: Optional[str] = Form(None, description="预览文本，使用声音档案时需要提供"),
    user_id: str = Depends(get_current_user_id)
):
    """
    创建数字人预览任务

    上传家长的正面照片，系统会使用阿里云 EMO 技术生成动态数字人预览视频。
    这是一个异步任务，创建后需要轮询 GET /preview/{task_id} 获取结果。

    **图片要求:**
    - 格式：JPG 或 PNG
    - 内容：清晰的正面人像照片
    - 大小：最大10MB

    **音频来源（三选一）:**
    1. **不传音频参数** - 使用系统默认音色生成预览
    2. **上传 audio 文件** - 直接使用上传的音频驱动数字人
    3. **传 voice_profile_id + preview_text** - 使用已保存的克隆声音合成音频

    **请求参数:**
    - **image**: 头像照片（multipart/form-data，必填）
    - **audio**: 音频文件（可选，WAV/MP3格式，最大20MB）
    - **voice_profile_id**: 声音档案ID（可选）
    - **preview_text**: 预览文本（使用声音档案时必填）

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "task_id": "user123_1703980800000",
            "status": "processing",
            "audio_source": "default",
            "message": "Digital human task created, poll for status"
        }
    }
    ```
    """

    # 验证图片文件类型
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式。支持的格式: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )

    # 验证文件大小 (最大 10MB)
    max_size = 10 * 1024 * 1024
    image_content = await image.read()
    if len(image_content) > max_size:
        raise HTTPException(status_code=400, detail="图片文件过大，最大支持 10MB")

    # 确定音频来源
    audio_source = AudioSourceType.DEFAULT
    audio_path = None
    audio_content = None

    if audio is not None:
        # 上传了音频文件
        if audio.content_type not in settings.ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的音频格式。支持的格式: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
            )
        audio_content = await audio.read()
        if len(audio_content) > 20 * 1024 * 1024:  # 20MB
            raise HTTPException(status_code=400, detail="音频文件过大，最大支持 20MB")
        audio_source = AudioSourceType.UPLOAD

    elif voice_profile_id:
        # 使用声音档案
        if not preview_text:
            raise HTTPException(
                status_code=400,
                detail="使用声音档案时必须提供 preview_text 参数"
            )
        audio_source = AudioSourceType.VOICE_PROFILE

    # 保存图片
    service = _get_service()
    image_path = service.save_image(
        user_id=user_id,
        file_content=image_content,
        filename=image.filename or "avatar.jpg"
    )

    # 保存音频（如果上传了）
    if audio_content:
        audio_path = service.save_audio(
            user_id=user_id,
            file_content=audio_content,
            filename=audio.filename or "audio.wav"
        )

    # 创建任务
    task_id = service.create_task(user_id)

    # 获取任务状态并更新（兼容本地和云端服务）
    task_status = service.get_task_status(task_id)
    if task_status:
        task_status["image_local"] = image_path
        task_status["audio_source"] = audio_source.value

    # 启动后台任务
    asyncio.create_task(
        service.generate_preview(
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
        "message": "数字人任务已创建，请轮询获取状态"
    })


@router.get("/preview/{task_id}", summary="获取数字人任务状态")
async def get_digital_human_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取数字人任务状态

    轮询此接口获取任务的处理进度和结果。
    建议轮询间隔：3-5秒（数字人生成较慢）。

    **路径参数:**
    - **task_id**: 任务ID（从 POST /preview 返回）

    **任务状态说明:**
    - **detecting**: 图像检测中，检测人脸和关键点
    - **generating**: 视频生成中，EMO 模型处理
    - **completed**: 完成，video_url 包含生成的视频
    - **failed**: 失败，error 包含错误信息

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "task_id": "user123_1703980800000",
            "status": "completed",
            "progress": 100,
            "video_url": "/uploads/avatar/user123/preview.mp4",
            "error": null
        }
    }
    ```
    """

    # 验证任务ID属于当前用户
    if not task_id.startswith(user_id):
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 获取任务状态
    service = _get_service()
    task = service.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

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

@router.post("/profiles", summary="保存头像档案")
async def save_avatar_profile(
    request: SaveAvatarProfileRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    保存头像档案

    数字人预览完成且满意后，将头像保存到头像档案库。
    保存后可在故事生成功能中重复使用该头像。

    **请求参数:**
    - **task_id**: 已完成的数字人任务ID
    - **name**: 头像名称，如：爸爸的头像、妈妈的头像

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "profile": {
                "id": "694534f1c32ffbd6151c18a4",
                "name": "爸爸的头像",
                "image_url": "/uploads/avatar/user123/photo.jpg",
                "preview_video_url": "/uploads/avatar/user123/preview.mp4",
                "created_at": "2025-01-01T12:00:00"
            }
        }
    }
    ```
    """
    service = _get_service()
    profile = await service.save_avatar_profile(
        user_id=user_id,
        task_id=request.task_id,
        name=request.name
    )

    if not profile:
        raise HTTPException(status_code=400, detail="无法保存头像档案，请确保任务已完成")

    return success_response({
        "profile": AvatarProfileResponse(
            id=profile["id"],
            name=profile["name"],
            image_url=profile["image_url"],
            preview_video_url=profile.get("preview_video_url"),
            created_at=profile["created_at"]
        ).model_dump()
    })


@router.get("/profiles", summary="获取头像档案列表")
async def get_avatar_profiles(
    user_id: str = Depends(get_current_user_id)
):
    """
    获取用户的所有头像档案

    返回当前用户保存的所有头像档案列表。
    这些头像可用于故事生成功能。

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "profiles": [
                {
                    "id": "694534f1c32ffbd6151c18a4",
                    "name": "爸爸的头像",
                    "image_url": "/uploads/avatar/user123/photo.jpg",
                    "preview_video_url": "/uploads/avatar/user123/preview.mp4",
                    "created_at": "2025-01-01T12:00:00"
                }
            ],
            "total": 2
        }
    }
    ```
    """
    service = _get_service()
    profiles = await service.get_user_avatar_profiles(user_id)

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


@router.get("/profiles/{profile_id}", summary="获取头像档案详情")
async def get_avatar_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取单个头像档案详情

    **路径参数:**
    - **profile_id**: 头像档案ID

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "694534f1c32ffbd6151c18a4",
            "name": "爸爸的头像",
            "image_url": "/uploads/avatar/user123/photo.jpg",
            "preview_video_url": "/uploads/avatar/user123/preview.mp4",
            "created_at": "2025-01-01T12:00:00"
        }
    }
    ```
    """
    service = _get_service()
    profile = await service.get_avatar_profile(profile_id, user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="头像档案不存在")

    return success_response(
        AvatarProfileResponse(
            id=profile["_id"],
            name=profile["name"],
            image_url=profile["image_url"],
            preview_video_url=profile.get("preview_video_url"),
            created_at=profile["created_at"]
        ).model_dump()
    )


@router.put("/profiles/{profile_id}", summary="更新头像档案")
async def update_avatar_profile(
    profile_id: str,
    request: UpdateAvatarProfileRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    更新头像档案名称

    **路径参数:**
    - **profile_id**: 头像档案ID

    **请求参数:**
    - **name**: 新的头像名称

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "更新成功",
        "data": null
    }
    ```
    """
    service = _get_service()
    success = await service.update_avatar_profile(
        profile_id=profile_id,
        user_id=user_id,
        name=request.name
    )

    if not success:
        raise HTTPException(status_code=404, detail="头像档案不存在或无权修改")

    return success_response(message="更新成功")


@router.delete("/profiles/{profile_id}", summary="删除头像档案")
async def delete_avatar_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    删除头像档案

    删除后将无法恢复，且使用该头像的历史记录不受影响。

    **路径参数:**
    - **profile_id**: 头像档案ID

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "删除成功",
        "data": null
    }
    ```
    """
    service = _get_service()
    success = await service.delete_avatar_profile(profile_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="头像档案不存在或无权删除")

    return success_response(message="删除成功")
