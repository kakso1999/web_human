"""检查最近的故事生成任务"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['echobot']

    # 获取最近10个任务
    cursor = db.story_generation_jobs.find(
        {},
        sort=[('created_at', -1)]
    ).limit(10)

    jobs = await cursor.to_list(length=10)
    print(f"Found {len(jobs)} recent jobs\n")

    for job in jobs:
        print("=" * 60)
        print(f'Job ID: {job["_id"]}')
        print(f'Status: {job.get("status")}')
        print(f'Error: {job.get("error")}')
        print(f'Current Step: {job.get("current_step")}')
        print(f'Progress: {job.get("progress")}')
        print(f'Dual Mode: {job.get("dual_mode")}')
        print(f'Final Video: {job.get("final_video_url")}')

        # Speaker configs
        speaker_configs = job.get('speaker_configs', [])
        print(f'\nSpeaker Configs ({len(speaker_configs)}):')
        for cfg in speaker_configs:
            print(f'  - {cfg.get("speaker_id")}: voice={cfg.get("voice_profile_id")}, avatar={cfg.get("avatar_profile_id")}')

        # 检查数字人任务详情
        dh_tasks = job.get('digital_human_tasks', [])
        print(f'\nDigital Human Tasks ({len(dh_tasks)}):')
        for task in dh_tasks:
            video_url = task.get("video_url", "No video")
            if video_url and len(video_url) > 80:
                video_url = video_url[:80] + "..."
            print(f'  - {task.get("speaker_id")} seg{task.get("segment_index")}: {task.get("status")} - {video_url}')
            if task.get('error'):
                print(f'    Error: {task.get("error")}')

        # 检查克隆语音任务
        voice_tasks = job.get('voice_clone_tasks', [])
        print(f'\nVoice Clone Tasks ({len(voice_tasks)}):')
        for task in voice_tasks:
            audio_url = task.get("audio_url", "No audio")
            if audio_url and len(audio_url) > 80:
                audio_url = audio_url[:80] + "..."
            print(f'  - {task.get("speaker_id")} seg{task.get("segment_index")}: {task.get("status")} - {audio_url}')

        print()

    client.close()

asyncio.run(check())
