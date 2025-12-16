"""
Admin 模块 - API 路由
管理后台接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
import os

from core.schemas.base import success_response
from core.schemas.pagination import paginate
from core.middleware.auth import require_admin
from core.config.settings import get_settings
from core.utils.helpers import generate_filename, ensure_dir

from modules.user.repository import UserRepository
from modules.story.service import get_story_service, StoryService
from modules.story.schemas import StoryCreate, StoryUpdate, CategoryCreate

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["管理后台"])


# ========== 数据统计 ==========

@router.get("/dashboard")
async def get_dashboard(
    _=Depends(require_admin)
):
    """获取数据概览"""
    user_repo = UserRepository()
    story_service = get_story_service()

    # 统计数据
    total_users = await user_repo.count()
    total_stories = await story_service.story_repo.count()
    published_stories = await story_service.story_repo.count({"is_published": True})

    return success_response({
        "total_users": total_users,
        "total_stories": total_stories,
        "published_stories": published_stories,
        # TODO: 添加更多统计数据
    })


# ========== 用户管理 ==========

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    _=Depends(require_admin)
):
    """获取用户列表"""
    user_repo = UserRepository()

    skip = (page - 1) * page_size
    users = await user_repo.list_users(
        skip=skip,
        limit=page_size,
        role=role,
        is_active=is_active,
        search=search
    )
    total = await user_repo.count_users(
        role=role,
        is_active=is_active,
        search=search
    )

    # 转换响应格式
    items = []
    for u in users:
        items.append({
            "id": u["id"],
            "email": u["email"],
            "nickname": u["nickname"],
            "avatar_url": u.get("avatar_url"),
            "role": u["role"],
            "subscription_plan": u.get("subscription", {}).get("plan", "free"),
            "is_active": u.get("is_active", True),
            "created_at": u["created_at"].isoformat() if u.get("created_at") else None,
            "last_login_at": u.get("last_login_at").isoformat() if u.get("last_login_at") else None
        })

    return paginate(items, total, page, page_size)


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    _=Depends(require_admin)
):
    """启用/禁用用户"""
    user_repo = UserRepository()
    await user_repo.update(user_id, {"is_active": is_active})
    return success_response(message="更新成功")


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    _=Depends(require_admin)
):
    """修改用户角色"""
    if role not in ["user", "subscriber", "admin"]:
        return {"code": 10001, "message": "无效的角色", "data": None}

    user_repo = UserRepository()
    await user_repo.update(user_id, {"role": role})
    return success_response(message="更新成功")


# ========== 分类管理 ==========

@router.post("/categories")
async def create_category(
    data: CategoryCreate,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """创建分类"""
    category = await story_service.create_category(data)
    return success_response(category.model_dump())


@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    data: CategoryCreate,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """更新分类"""
    await story_service.category_repo.update(category_id, data.model_dump())
    category = await story_service.category_repo.get_by_id(category_id)
    return success_response(category)


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """删除分类"""
    await story_service.category_repo.delete(category_id)
    return success_response(message="删除成功")


# ========== 故事管理 ==========

@router.get("/stories")
async def list_stories_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    is_published: Optional[bool] = None,
    search: Optional[str] = None,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """获取故事列表（包含未发布的）"""
    result = await story_service.list_stories(
        page=page,
        page_size=page_size,
        category_id=category_id,
        is_published=is_published,
        search=search
    )
    return result


@router.post("/stories")
async def create_story(
    data: StoryCreate,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """创建故事"""
    story = await story_service.create_story(data)
    return success_response(story.model_dump())


@router.put("/stories/{story_id}")
async def update_story(
    story_id: str,
    data: StoryUpdate,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """更新故事"""
    story = await story_service.update_story(story_id, data)
    return success_response(story.model_dump())


@router.delete("/stories/{story_id}")
async def delete_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """删除故事"""
    await story_service.delete_story(story_id)
    return success_response(message="删除成功")


@router.post("/stories/{story_id}/publish")
async def publish_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """发布故事"""
    await story_service.story_repo.update(story_id, {"is_published": True})
    return success_response(message="发布成功")


@router.post("/stories/{story_id}/unpublish")
async def unpublish_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """下架故事"""
    await story_service.story_repo.update(story_id, {"is_published": False})
    return success_response(message="下架成功")


# ========== 文件上传 ==========

@router.post("/upload/thumbnail")
async def upload_thumbnail(
    file: UploadFile = File(...),
    _=Depends(require_admin)
):
    """上传故事缩略图"""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        return {"code": 10001, "message": "不支持的图片格式", "data": None}

    filename = generate_filename(file.filename)
    upload_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
    ensure_dir(upload_dir)

    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    url = f"/uploads/thumbnails/{filename}"
    return success_response({"url": url})


@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    _=Depends(require_admin)
):
    """上传故事视频"""
    if file.content_type not in settings.ALLOWED_VIDEO_TYPES:
        return {"code": 10001, "message": "不支持的视频格式", "data": None}

    filename = generate_filename(file.filename)
    upload_dir = os.path.join(settings.UPLOAD_DIR, "videos")
    ensure_dir(upload_dir)

    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    url = f"/uploads/videos/{filename}"
    return success_response({"url": url})
