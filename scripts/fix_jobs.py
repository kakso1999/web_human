"""修复任务队列 - 取消旧任务"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

async def check_and_fix():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME")]

    # 查看所有未完成的任务
    cursor = db.story_jobs.find({"status": {"$in": ["pending", "processing"]}})
    jobs = await cursor.to_list(100)

    print("未完成的任务:")
    for job in jobs:
        print(f"  {job['_id']}: status={job['status']}, max_segments={job.get('max_segments')}, step={job.get('current_step')}")

    # 取消旧任务 (没有 max_segments 的)
    old_job_id = "6970986cade8f484a78dfe52"
    result = await db.story_jobs.update_one(
        {"_id": ObjectId(old_job_id)},
        {"$set": {"status": "failed", "error": "手动取消 - 切换到新测试任务"}}
    )
    print(f"\n已取消旧任务 {old_job_id}: modified={result.modified_count}")

    # 再次查看
    cursor = db.story_jobs.find({"status": {"$in": ["pending", "processing"]}})
    jobs = await cursor.to_list(100)
    print("\n当前未完成的任务:")
    for job in jobs:
        print(f"  {job['_id']}: status={job['status']}, max_segments={job.get('max_segments')}")

    client.close()

if __name__ == "__main__":
    asyncio.run(check_and_fix())
