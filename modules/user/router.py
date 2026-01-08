"""
User 模块 - API 路由
用户资料相关接口
"""
from fastapi import APIRouter, Depends, UploadFile, File
import os

from core.schemas.base import success_response
from core.middleware.auth import get_current_user_id
from core.config.settings import get_settings
from core.utils.helpers import generate_filename, ensure_dir

from modules.user.schemas import UpdateProfileRequest, ChangePasswordRequest
from modules.user.service import get_user_service, UserService

settings = get_settings()
router = APIRouter(prefix="/user", tags=["用户"])


@router.get("/profile", summary="获取用户资料")
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取当前登录用户的个人资料

    返回用户的基本信息、订阅状态等。

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "6948bda91fd873cf81f5addd",
            "email": "user@example.com",
            "nickname": "小明",
            "avatar_url": "https://example.com/avatar.jpg",
            "role": "user",
            "subscription": {"plan": "free", "expires_at": null},
            "is_active": true,
            "created_at": "2025-01-01T12:00:00"
        }
    }
    ```
    """
    profile = await user_service.get_profile(user_id)
    return success_response(profile.model_dump())


@router.put("/profile", summary="更新用户资料")
async def update_profile(
    data: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """
    更新当前用户的个人资料

    可更新的字段：
    - **nickname**: 用户昵称

    **请求示例:**
    ```json
    {
        "nickname": "新昵称"
    }
    ```
    """
    profile = await user_service.update_profile(user_id, data)
    return success_response(profile.model_dump())


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片文件，支持 JPG/PNG/GIF/WebP 格式"),
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """
    上传用户头像

    **支持的图片格式:** JPG, PNG, GIF, WebP

    **文件大小限制:** 最大 5MB

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "6948bda91fd873cf81f5addd",
            "avatar_url": "/uploads/avatars/user123/avatar_20250101.jpg",
            ...
        }
    }
    ```
    """
    # 验证文件类型
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        return {"code": 10001, "message": "不支持的图片格式", "data": None}

    # 生成文件名和路径
    filename = generate_filename(file.filename)
    upload_dir = os.path.join(settings.UPLOAD_DIR, "avatars", user_id)
    ensure_dir(upload_dir)

    file_path = os.path.join(upload_dir, filename)

    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 生成 URL
    avatar_url = f"/uploads/avatars/{user_id}/{filename}"

    # 更新用户头像
    profile = await user_service.update_avatar(user_id, avatar_url)

    return success_response(profile.model_dump())


@router.post("/change-password", summary="修改密码")
async def change_password(
    data: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """
    修改当前用户的登录密码

    需要提供当前密码进行验证，新密码必须满足以下要求：
    - 长度至少8位
    - 包含至少一个大写字母
    - 包含至少一个小写字母
    - 包含至少一个数字

    **请求示例:**
    ```json
    {
        "old_password": "OldPassword123",
        "new_password": "NewPassword456"
    }
    ```

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "密码修改成功",
        "data": null
    }
    ```
    """
    await user_service.change_password(
        user_id,
        data.old_password,
        data.new_password
    )
    return success_response(message="密码修改成功")
