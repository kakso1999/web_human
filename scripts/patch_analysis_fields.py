"""
为已分析的故事补充 single_speaker_analysis 和 dual_speaker_analysis 字段
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.database import Database


async def patch_stories():
    await Database.connect()
    db = Database.get_db()

    # 查找已分析但缺少新字段的故事
    stories = await db.stories.find({
        'is_analyzed': True,
        '$or': [
            {'single_speaker_analysis': {'$exists': False}},
            {'dual_speaker_analysis': {'$exists': False}}
        ]
    }).to_list(100)

    print(f'找到 {len(stories)} 个需要补充字段的故事')

    for s in stories:
        story_id = str(s['_id'])
        subtitles = s.get('subtitles', [])
        speakers = s.get('speakers', [])

        # 计算总时长
        total_duration = sum(seg.get('end', 0) - seg.get('start', 0) for seg in subtitles) if subtitles else 0

        update_data = {
            'single_speaker_analysis': {
                'is_analyzed': True,
                'vocals_url': None,
                'background_url': None,
                'duration': total_duration
            },
            'dual_speaker_analysis': {
                'is_analyzed': True,
                'speakers': speakers,
                'background_url': None,
                'diarization_segments': subtitles
            }
        }

        await db.stories.update_one({'_id': s['_id']}, {'$set': update_data})
        print(f'  已更新: {story_id} - {s.get("title_en") or s.get("title")}')

    await Database.disconnect()
    print('\n补充完成!')


if __name__ == '__main__':
    asyncio.run(patch_stories())
