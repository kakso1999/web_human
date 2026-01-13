import asyncio
import sys
import os
import time

sys.path.insert(0, 'E:/工作代码/73_web_human')
os.chdir('E:/工作代码/73_web_human')

async def run_job():
    from core.config.database import Database
    from modules.story_generation.service import StoryGenerationService

    await Database.connect()
    print('MongoDB connected')

    service = StoryGenerationService()
    job_id = '6963accc6e95a465a42198a2'

    print(f'Processing job {job_id}...')
    print('This may take 10-15 minutes for dual-speaker mode')
    print()

    start = time.time()

    try:
        await service._process_job_multi_speaker(job_id)
        print('\n[SUCCESS] Job completed!')
    except Exception as e:
        print(f'\n[ERROR] Job failed: {e}')
        import traceback
        traceback.print_exc()

    elapsed = time.time() - start
    print(f'\nTotal time: {elapsed/60:.1f} minutes')

    # Get final status
    from bson import ObjectId
    db = Database.get_db()
    job = await db.story_jobs.find_one({'_id': ObjectId(job_id)})
    print(f'Status: {job.get("status")}')
    print(f'Progress: {job.get("progress")}%')
    print(f'Step: {job.get("current_step")}')
    if job.get('final_video_url'):
        print(f'Final video: {job.get("final_video_url")}')
    if job.get('error'):
        print(f'Error: {job.get("error")}')

if __name__ == '__main__':
    asyncio.run(run_job())
