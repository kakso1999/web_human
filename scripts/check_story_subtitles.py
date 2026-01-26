"""检查故事数据中的字幕和说话人分配"""
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
import json

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['echobot']

    # 获取最近的故事
    story = await db.stories.find_one(
        {},
        sort=[('created_at', -1)]
    )

    if story:
        print(f"Story ID: {story['_id']}")
        print(f"Title: {story.get('title')}")

        # 检查 dual_speaker_analysis
        dual_analysis = story.get('dual_speaker_analysis', {})
        print(f"\n=== dual_speaker_analysis ===")
        print(f"is_analyzed: {dual_analysis.get('is_analyzed')}")

        # 检查 speakers 数组
        speakers = dual_analysis.get('speakers', [])
        print(f"\nSpeakers ({len(speakers)}):")
        for i, spk in enumerate(speakers):
            print(f"  Speaker {i+1}:")
            print(f"    speaker_id: {spk.get('speaker_id')}")
            print(f"    label: {spk.get('label')}")
            print(f"    duration: {spk.get('duration')}")
            print(f"    gender: {spk.get('gender')}")
            print(f"    audio_url: {spk.get('audio_url', 'N/A')[:50] if spk.get('audio_url') else 'N/A'}...")

    else:
        print("No story found")

    client.close()

asyncio.run(check())
