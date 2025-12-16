"""
基础仓储类
提供 MongoDB CRUD 操作的基类
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from core.config.database import Database

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """基础仓储类，提供通用 CRUD 操作"""

    collection_name: str = ""

    def __init__(self):
        if not self.collection_name:
            raise ValueError("必须指定 collection_name")

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """获取集合"""
        return Database.get_collection(self.collection_name)

    async def create(self, data: Dict[str, Any]) -> str:
        """
        创建文档

        Args:
            data: 文档数据

        Returns:
            插入的文档 ID
        """
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取文档

        Args:
            id: 文档 ID

        Returns:
            文档数据或 None
        """
        if not ObjectId.is_valid(id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(id)})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def get_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        根据条件获取单个文档

        Args:
            filter: 查询条件

        Returns:
            文档数据或 None
        """
        doc = await self.collection.find_one(filter)
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def get_many(
        self,
        filter: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 20,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        获取多个文档

        Args:
            filter: 查询条件
            skip: 跳过数量
            limit: 限制数量
            sort: 排序规则，如 [("created_at", -1)]

        Returns:
            文档列表
        """
        filter = filter or {}
        cursor = self.collection.find(filter)

        if sort:
            cursor = cursor.sort(sort)

        cursor = cursor.skip(skip).limit(limit)

        docs = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            docs.append(doc)

        return docs

    async def count(self, filter: Dict[str, Any] = None) -> int:
        """
        统计文档数量

        Args:
            filter: 查询条件

        Returns:
            文档数量
        """
        filter = filter or {}
        return await self.collection.count_documents(filter)

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """
        更新文档

        Args:
            id: 文档 ID
            data: 更新数据

        Returns:
            是否更新成功
        """
        if not ObjectId.is_valid(id):
            return False

        data["updated_at"] = datetime.utcnow()

        # 移除不应更新的字段
        data.pop("_id", None)
        data.pop("id", None)
        data.pop("created_at", None)

        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0

    async def delete(self, id: str) -> bool:
        """
        删除文档

        Args:
            id: 文档 ID

        Returns:
            是否删除成功
        """
        if not ObjectId.is_valid(id):
            return False

        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def exists(self, filter: Dict[str, Any]) -> bool:
        """
        检查文档是否存在

        Args:
            filter: 查询条件

        Returns:
            是否存在
        """
        count = await self.collection.count_documents(filter, limit=1)
        return count > 0
