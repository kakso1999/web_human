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


@router.get("/profile")
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """获取当前用户资料"""
    profile = await user_service.get_profile(user_id)
    return success_response(profile.model_dump())


@router.put("/profile")
async def update_profile(
    data: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户资料"""
    profile = await user_service.update_profile(user_id, data)
    return success_response(profile.model_dump())


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """上传头像"""
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


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """修改密码"""
    await user_service.change_password(
        user_id,
        data.old_password,
        data.new_password
    )
    return success_response(message="密码修改成功")
