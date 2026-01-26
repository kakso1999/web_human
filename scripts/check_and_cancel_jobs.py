"""
检查所有任务状态
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from core.config.database import Database


async def main():
    await Database.connect()
    db = Database.get_db()

    # 查找所有任务（最近20个）
    jobs = await db.story_generation_jobs.find({}).sort('created_at', -1).to_list(20)

    print(f"最近 {len(jobs)} 个任务:")
    for job in jobs:
        job_id = str(job["_id"])
        status = job["status"]
        step = job.get("current_step", "N/A")
        error = job.get("error", "")[:50] if job.get("error") else ""
        created = job.get("created_at", "N/A")
        print(f"  - {job_id}: status={status}, step={step}, error={error}")


if __name__ == "__main__":
    asyncio.run(main())
