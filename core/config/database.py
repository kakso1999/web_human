"""
数据库配置模块
MongoDB 连接配置和客户端管理
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from core.config.settings import get_settings

settings = get_settings()


class Database:
    """MongoDB 数据库管理类"""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """连接数据库"""
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls.db = cls.client[settings.MONGODB_DB_NAME]

        # 验证连接
        try:
            await cls.client.admin.command('ping')
            print(f"MongoDB 连接成功: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            print(f"MongoDB 连接失败: {e}")
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """断开数据库连接"""
        if cls.client:
            cls.client.close()
            print("MongoDB 连接已关闭")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """获取数据库实例"""
        if cls.db is None:
            raise RuntimeError("数据库未连接，请先调用 Database.connect()")
        return cls.db

    @classmethod
    def get_collection(cls, name: str):
        """获取集合"""
        return cls.get_db()[name]


# 便捷函数
def get_database() -> AsyncIOMotorDatabase:
    """依赖注入用：获取数据库实例"""
    return Database.get_db()
