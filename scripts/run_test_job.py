import asyncio
import sys
import os
import time

sys.path.insert(0, 'E:/工作代码/73_web_human')
os.chdir('E:/工作代码/73_web_human')

# 应用 DNS 补丁（必须在导入其他模块之前）
from core.utils.dns_patch import patch_dns

async def run():
    from core.config.database import Database
    from modules.story_generation.service import StoryGenerationService
    from bson import ObjectId

    await Database.connect()
    print('MongoDB connected')

    service = StoryGenerationService()

    user_id = '6940d02e190796e180c54ae7'
    story_id = '6960c86bbb273d8a0dcfafe7'
    voice_profile_id = '694f45e92c1e9fc23947aea5'
    avatar_profile_id = '694f47f41fd5d81372fe8464'

    # 双说话人配置
    speaker_configs = [
        {'speaker_id': 'SPEAKER_00', 'voice_profile_id': voice_profile_id, 'avatar_profile_id': avatar_profile_id, 'enabled': True},
        {'speaker_id': 'SPEAKER_01', 'voice_profile_id': voice_profile_id, 'avatar_profile_id': avatar_profile_id, 'enabled': True}
    ]

    print('Creating new job...')
    result = await service.create_job(
        user_id=user_id,
        story_id=story_id,
        mode='dual',
        speaker_configs=speaker_configs,
        full_video=True
    )
    job_id = result['id']
    print(f'Job created: {job_id}')
    print('Backend will process job in background...')
    print()

    start = time.time()
    db = Database.get_db()

    # 监控任务进度
    last_step = None
    last_progress = None
    while True:
        job = await db.story_jobs.find_one({'_id': ObjectId(job_id)})
        if not job:
            print('Job not found!')
            break

        status = job.get('status')
        progress = job.get('progress', 0)
        step = job.get('current_step', '')
        error = job.get('error')

        # 打印进度变化
        if step != last_step or progress != last_progress:
            elapsed = time.time() - start
            print(f'[{elapsed:.0f}s] Status: {status}, Progress: {progress}%, Step: {step}')
            last_step = step
            last_progress = progress

        # 检查是否完成或失败
        if status == 'completed':
            print(f'\n[SUCCESS] Job completed!')
            if job.get('final_video_url'):
                print(f'Final video: {job.get("final_video_url")}')
            break
        elif status == 'failed':
            print(f'\n[FAILED] Job failed!')
            if error:
                print(f'Error: {error}')
            break

        await asyncio.sleep(5)  # 每5秒检查一次

    elapsed = time.time() - start
    print(f'\nTotal time: {elapsed/60:.1f} minutes')

if __name__ == '__main__':
    asyncio.run(run())
