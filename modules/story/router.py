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

@router.get("/categories", summary="获取故事分类列表")
async def list_categories(
    story_service: StoryService = Depends(get_story_service)
):
    """
    获取所有故事分类

    返回平台上所有可用的故事分类，按排序字段排列。
    用于前端分类筛选和导航。

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": "694534f1c32ffbd6151c18a1",
                "name": "童话故事",
                "name_en": "Fairy Tales",
                "sort_order": 0,
                "story_count": 15
            }
        ]
    }
    ```
    """
    categories = await story_service.list_categories()
    return success_response([c.model_dump() for c in categories])


# ========== 故事接口 ==========

@router.get("", summary="获取故事列表")
async def list_stories(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    category_id: Optional[str] = Query(None, description="分类ID，用于筛选特定分类"),
    search: Optional[str] = Query(None, description="搜索关键词，匹配标题"),
    story_service: StoryService = Depends(get_story_service)
):
    """
    获取已发布的故事列表

    支持分页、分类筛选和关键词搜索。
    普通用户只能查看已发布状态的故事。

    **请求参数:**
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，1-100
    - **category_id**: 分类ID（可选），筛选特定分类下的故事
    - **search**: 搜索关键词（可选），匹配故事标题

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": "694534f1c32ffbd6151c18a2",
                    "title": "三只小猪",
                    "title_en": "The Three Little Pigs",
                    "category_id": "694534f1c32ffbd6151c18a1",
                    "thumbnail_url": "/uploads/thumbnails/story123.jpg",
                    "duration": 180,
                    "is_published": true,
                    "view_count": 1234,
                    "created_at": "2025-01-01T12:00:00"
                }
            ],
            "total": 50,
            "page": 1,
            "page_size": 20
        }
    }
    ```
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


@router.get("/random", summary="获取随机故事")
async def get_random_stories(
    limit: int = Query(10, ge=1, le=20, description="返回数量，最大20"),
    story_service: StoryService = Depends(get_story_service)
):
    """
    获取随机故事列表

    随机返回指定数量的已发布故事，用于首页轮播图和推荐展示。

    **请求参数:**
    - **limit**: 返回数量，1-20，默认10

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": "694534f1c32ffbd6151c18a2",
                "title": "三只小猪",
                "thumbnail_url": "/uploads/thumbnails/story123.jpg",
                "duration": 180
            }
        ]
    }
    ```
    """
    stories = await story_service.get_random_stories(limit)
    return success_response([s.model_dump() for s in stories])


@router.get("/{story_id}", summary="获取故事详情")
async def get_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service)
):
    """
    获取单个故事的完整详情

    返回故事的所有信息，包括视频URL、字幕数据等。

    **路径参数:**
    - **story_id**: 故事唯一标识ID

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "694534f1c32ffbd6151c18a2",
            "title": "三只小猪",
            "title_en": "The Three Little Pigs",
            "category_id": "694534f1c32ffbd6151c18a1",
            "category_name": "童话故事",
            "description": "三只小猪建房子的经典童话故事",
            "thumbnail_url": "/uploads/thumbnails/story123.jpg",
            "video_url": "/uploads/videos/story123.mp4",
            "audio_url": "/uploads/audio/story123.mp3",
            "duration": 180,
            "is_published": true,
            "view_count": 1234,
            "subtitles": [
                {"start": 0.0, "end": 3.5, "text": "从前有三只小猪..."}
            ],
            "created_at": "2025-01-01T12:00:00",
            "updated_at": "2025-01-01T12:00:00"
        }
    }
    ```
    """
    story = await story_service.get_story(story_id)
    return success_response(story.model_dump())


@router.post("/{story_id}/view", summary="记录播放次数")
async def record_view(
    story_id: str,
    story_service: StoryService = Depends(get_story_service)
):
    """
    记录故事播放次数

    每次用户观看故事时调用此接口，用于统计播放量。

    **路径参数:**
    - **story_id**: 故事唯一标识ID

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "播放记录成功",
        "data": null
    }
    ```
    """
    await story_service.increment_view(story_id)
    return success_response(message="播放记录成功")
