"""取消所有进行中的任务"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

async def cancel_all():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME")]

    # 取消所有正在处理和等待中的任务
    result = await db.story_jobs.update_many(
        {"status": {"$in": ["pending", "processing"]}},
        {"$set": {"status": "failed", "error": "手动取消 - 重新测试"}}
    )
    print(f"取消了 {result.modified_count} 个任务")

    client.close()

if __name__ == "__main__":
    asyncio.run(cancel_all())
