"""修复现有故事的说话人时长数据"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def fix_durations():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['echobot']

    # 获取所有已分析的故事
    cursor = db.stories.find({'is_analyzed': True})
    stories = await cursor.to_list(length=100)

    print(f"Found {len(stories)} analyzed stories")

    for story in stories:
        story_id = story['_id']
        subtitles = story.get('subtitles', [])

        if not subtitles:
            print(f"  {story_id}: No subtitles, skipping")
            continue

        # 计算每个配音角色的时长
        voice_durations = {'VOICE_1': 0.0, 'VOICE_2': 0.0}
        for seg in subtitles:
            voice = seg.get('voice', 'VOICE_1')
            seg_duration = seg.get('end', 0) - seg.get('start', 0)
            if voice in voice_durations:
                voice_durations[voice] += seg_duration

        print(f"  {story_id}: VOICE_1={voice_durations['VOICE_1']:.1f}s, VOICE_2={voice_durations['VOICE_2']:.1f}s")

        # 更新 dual_speaker_analysis.speakers 中的 duration
        dual_analysis = story.get('dual_speaker_analysis', {})
        speakers = dual_analysis.get('speakers', [])

        if speakers:
            for spk in speakers:
                voice_id = spk.get('speaker_id')
                if voice_id in voice_durations:
                    spk['duration'] = round(voice_durations[voice_id], 1)

            # 更新数据库
            await db.stories.update_one(
                {'_id': story_id},
                {'$set': {'dual_speaker_analysis.speakers': speakers}}
            )
            print(f"    Updated!")

        # 同时更新顶级 speakers 字段（如果存在）
        top_speakers = story.get('speakers', [])
        if top_speakers:
            for spk in top_speakers:
                voice_id = spk.get('speaker_id')
                if voice_id in voice_durations:
                    spk['duration'] = round(voice_durations[voice_id], 1)

            await db.stories.update_one(
                {'_id': story_id},
                {'$set': {'speakers': top_speakers}}
            )

    print("\nDone!")
    client.close()

asyncio.run(fix_durations())
