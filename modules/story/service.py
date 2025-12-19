"""
Story 模块 - 业务逻辑层
"""
from typing import Optional, List
from core.exceptions.handlers import NotFoundException
from core.schemas.pagination import paginate

from modules.story.repository import StoryRepository, CategoryRepository
from modules.story.schemas import (
    StoryCreate, StoryUpdate, StoryResponse, StoryListItem,
    CategoryCreate, CategoryResponse
)


class StoryService:
    """故事服务"""

    def __init__(self):
        self.story_repo = StoryRepository()
        self.category_repo = CategoryRepository()

    # ========== 分类相关 ==========

    async def list_categories(self) -> List[CategoryResponse]:
        """获取所有分类"""
        categories = await self.category_repo.list_all()
        return [CategoryResponse(
            id=c["id"],
            name=c["name"],
            name_en=c["name_en"],
            sort_order=c.get("sort_order", 0),
            story_count=c.get("story_count", 0)
        ) for c in categories]

    async def create_category(self, data: CategoryCreate) -> CategoryResponse:
        """创建分类"""
        category_data = data.model_dump()
        category_data["story_count"] = 0
        category_id = await self.category_repo.create(category_data)
        category = await self.category_repo.get_by_id(category_id)
        return CategoryResponse(
            id=category["id"],
            name=category["name"],
            name_en=category["name_en"],
            sort_order=category.get("sort_order", 0),
            story_count=0
        )

    # ========== 故事相关 ==========

    async def list_stories(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[str] = None,
        is_published: Optional[bool] = None,
        search: Optional[str] = None
    ) -> dict:
        """获取故事列表"""
        skip = (page - 1) * page_size

        stories = await self.story_repo.list_stories(
            skip=skip,
            limit=page_size,
            category_id=category_id,
            is_published=is_published,
            search=search
        )

        total = await self.story_repo.count_stories(
            category_id=category_id,
            is_published=is_published,
            search=search
        )

        items = [StoryListItem(
            id=s["id"],
            title=s["title"],
            title_en=s.get("title_en"),
            category_id=s["category_id"],
            thumbnail_url=s.get("thumbnail_url"),
            duration=s.get("duration", 0),
            is_published=s.get("is_published", False),
            is_processing=s.get("is_processing", False),
            view_count=s.get("view_count", 0),
            created_at=s["created_at"]
        ).model_dump() for s in stories]

        return paginate(items, total, page, page_size)

    async def get_story(self, story_id: str) -> StoryResponse:
        """��取故事详情"""
        story = await self.story_repo.get_by_id(story_id)

        if not story:
            raise NotFoundException("故事不存在")

        return StoryResponse(
            id=story["id"],
            title=story["title"],
            title_en=story.get("title_en"),
            category_id=story["category_id"],
            description=story.get("description"),
            description_en=story.get("description_en"),
            thumbnail_url=story.get("thumbnail_url"),
            video_url=story.get("video_url"),
            audio_url=story.get("audio_url"),
            duration=story.get("duration", 0),
            is_published=story.get("is_published", False),
            is_processing=story.get("is_processing", False),
            view_count=story.get("view_count", 0),
            subtitles=story.get("subtitles"),
            subtitle_text=story.get("subtitle_text"),
            created_at=story["created_at"],
            updated_at=story["updated_at"]
        )

    async def create_story(self, data: StoryCreate) -> StoryResponse:
        """创建故事"""
        story_data = data.model_dump()
        story_data["view_count"] = 0
        story_id = await self.story_repo.create(story_data)

        # 更新分类的故事数量
        await self.category_repo.increment_story_count(data.category_id, 1)

        return await self.get_story(story_id)

    async def update_story(self, story_id: str, data: StoryUpdate) -> StoryResponse:
        """更新故事"""
        story = await self.story_repo.get_by_id(story_id)
        if not story:
            raise NotFoundException("故事不存在")

        update_data = data.model_dump(exclude_none=True)

        # 如果更换了分类，更新分类的故事数量
        if "category_id" in update_data and update_data["category_id"] != story["category_id"]:
            await self.category_repo.increment_story_count(story["category_id"], -1)
            await self.category_repo.increment_story_count(update_data["category_id"], 1)

        await self.story_repo.update(story_id, update_data)
        return await self.get_story(story_id)

    async def delete_story(self, story_id: str) -> bool:
        """删除故事"""
        story = await self.story_repo.get_by_id(story_id)
        if not story:
            raise NotFoundException("故事不存在")

        # 更新分类的故事数量
        await self.category_repo.increment_story_count(story["category_id"], -1)

        return await self.story_repo.delete(story_id)

    async def increment_view(self, story_id: str) -> bool:
        """增加播放次数"""
        return await self.story_repo.increment_view_count(story_id)

    async def get_random_stories(self, limit: int = 10) -> List[StoryListItem]:
        """获取随机故事（用于轮播图）"""
        stories = await self.story_repo.get_random_stories(limit)
        return [StoryListItem(
            id=s["id"],
            title=s["title"],
            title_en=s.get("title_en"),
            category_id=s["category_id"],
            thumbnail_url=s.get("thumbnail_url"),
            duration=s.get("duration", 0),
            is_published=True,
            view_count=s.get("view_count", 0),
            created_at=s["created_at"]
        ) for s in stories]


_story_service: Optional[StoryService] = None


def get_story_service() -> StoryService:
    """获取故事服务"""
    global _story_service
    if _story_service is None:
        _story_service = StoryService()
    return _story_service
