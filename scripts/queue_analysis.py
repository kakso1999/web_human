"""
将未分析的故事加入分析队列
"""
import asyncio
import os
import sys

# 设置环境变量
os.environ['APIMART_API_KEY'] = 'sk-UDeD65vQO0kV7sd861RAFzLtdi4sdDYAUSrPMyOY8NIO11Zm'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.database import Database
from core.config.settings import get_settings
from modules.story.analysis_queue import get_analysis_queue, start_analysis_worker

settings = get_settings()


async def queue_unanalyzed_stories():
    await Database.connect()
    db = Database.get_db()

    # 获取未分析的故事
    stories = await db.stories.find({
        'is_analyzed': False
    }).sort('created_at', 1).to_list(100)

    print(f'找到 {len(stories)} 个未分析故事')

    if not stories:
        print('没有待分析的故事')
        await Database.disconnect()
        return

    # 启动队列工作者
    await start_analysis_worker()

    queue = get_analysis_queue()

    for s in stories:
        story_id = str(s['_id'])
        video_url = s.get('video_url', '')

        if video_url.startswith('/uploads/'):
            video_path = os.path.join(settings.UPLOAD_DIR, video_url[9:])
        else:
            video_path = video_url

        if not os.path.exists(video_path):
            print(f'跳过 {story_id}: 视频不存在')
            continue

        queue_size = await queue.add_task(story_id, video_path)
        print(f'已加入队列: {story_id}, 队列大小: {queue_size}')

    print(f'\n队列大小: {queue.get_queue_size()}')
    print('等待队列处理完成...')

    # 等待队列处理完成
    while queue.get_queue_size() > 0 or queue.get_current_task():
        current = queue.get_current_task()
        if current:
            print(f'  正在处理: {current}, 队列剩余: {queue.get_queue_size()}')
        await asyncio.sleep(5)

    print('\n所有任务处理完成!')
    await Database.disconnect()


if __name__ == '__main__':
    asyncio.run(queue_unanalyzed_stories())
