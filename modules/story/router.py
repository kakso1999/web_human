"""
Story 模块 - API 路由
故事相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from core.schemas.base import success_response
from core.middleware.auth import get_current_user_optional

from modules.story.schemas import StoryCreate, StoryUpdate, CategoryCreate
from modules.story.service import get_story_service, StoryService

router = APIRouter(prefix="/stories", tags=["故事"])


# ========== 分类接口 ==========

@router.get("/categories")
async def list_categories(
    story_service: StoryService = Depends(get_story_service)
):
    """获取所有分类"""
    categories = await story_service.list_categories()
    return success_response([c.model_dump() for c in categories])


# ========== 故事接口 ==========

@router.get("")
async def list_stories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    story_service: StoryService = Depends(get_story_service)
):
    """
    获取故事列表

    - **page**: 页码
    - **page_size**: 每页数量
    - **category_id**: 分类ID（可选）
    - **search**: 搜索关键词（可选）
    """
    # 普通用户只能看到已发布的故事
    result = await story_service.list_stories(
        page=page,
        page_size=page_size,
        category_id=category_id,
        is_published=True,
        search=search
    )
    return result


@router.get("/random")
async def get_random_stories(
    limit: int = Query(10, ge=1, le=20),
    story_service: StoryService = Depends(get_story_service)
):
    """获取随机故事（用于首页轮播图）"""
    stories = await story_service.get_random_stories(limit)
    return success_response([s.model_dump() for s in stories])


@router.get("/{story_id}")
async def get_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service)
):
    """获取故事详情"""
    story = await story_service.get_story(story_id)
    return success_response(story.model_dump())


@router.post("/{story_id}/view")
async def record_view(
    story_id: str,
    story_service: StoryService = Depends(get_story_service)
):
    """记录播放次数"""
    await story_service.increment_view(story_id)
    return success_response(message="播放记录成功")
