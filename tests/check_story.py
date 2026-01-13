"""
检查故事数据
"""
import asyncio
import sys
import os

sys.path.insert(0, 'E:/工作代码/73_web_human')
os.chdir('E:/工作代码/73_web_human')

async def check():
    from core.config.database import Database
    from bson import ObjectId

    await Database.connect()
    print('MongoDB connected')

    db = Database.get_db()

    story_id = '6960c86bbb273d8a0dcfafe7'
    story = await db.stories.find_one({'_id': ObjectId(story_id)})

    if story:
        print(f'\nStory: {story.get("title")}')
        print(f'Video URL: {story.get("video_url")}')
        print(f'Thumbnail: {story.get("thumbnail_url")}')

        # 检查视频文件是否存在
        video_url = story.get("video_url")
        if video_url:
            if video_url.startswith('/'):
                video_path = f'E:/工作代码/73_web_human/uploads{video_url}'
            else:
                video_path = video_url

            print(f'\nVideo path: {video_path}')
            if os.path.exists(video_path):
                print(f'File exists: YES ({os.path.getsize(video_path)/1024/1024:.1f} MB)')
            else:
                print(f'File exists: NO')
    else:
        print(f'Story not found: {story_id}')

if __name__ == '__main__':
    asyncio.run(check())
