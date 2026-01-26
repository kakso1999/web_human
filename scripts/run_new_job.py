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

    print('Processing job...')
    print('This may take 10-15 minutes')
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
    asyncio.run(run())
