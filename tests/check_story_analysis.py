"""
诊断脚本：检查故事分析状态

使用方法：
python tests/check_story_analysis.py <story_id>
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def check_story(story_id: str):
    from modules.story.repository import StoryRepository

    repo = StoryRepository()
    story = await repo.get_by_id(story_id)

    if not story:
        print(f"[ERROR] 故事 {story_id} 不存在")
        return

    print(f"\n=== 故事信息 ===")
    print(f"ID: {story.get('id')}")
    print(f"标题: {story.get('title')}")
    print(f"视频URL: {story.get('video_url')}")
    print(f"is_processing: {story.get('is_processing')}")
    print(f"is_analyzed: {story.get('is_analyzed')}")
    print(f"analysis_error: {story.get('analysis_error')}")

    print(f"\n=== 单人模式分析 ===")
    single = story.get('single_speaker_analysis')
    if single:
        print(f"  is_analyzed: {single.get('is_analyzed')}")
        print(f"  vocals_url: {single.get('vocals_url')}")
        print(f"  background_url: {single.get('background_url')}")
        print(f"  duration: {single.get('duration')}")
    else:
        print("  [未分析] single_speaker_analysis 为空")

    print(f"\n=== 双人模式分析 ===")
    dual = story.get('dual_speaker_analysis')
    if dual:
        print(f"  is_analyzed: {dual.get('is_analyzed')}")
        print(f"  speakers: {len(dual.get('speakers', []))} 个说话人")
        for spk in dual.get('speakers', []):
            print(f"    - {spk.get('speaker_id')}: {spk.get('label')}, duration={spk.get('duration')}s")
        print(f"  background_url: {dual.get('background_url')}")
        print(f"  diarization_segments: {len(dual.get('diarization_segments', []))} 个片段")
    else:
        print("  [未分析] dual_speaker_analysis 为空")

    # 旧字段兼容
    print(f"\n=== 旧字段 (向后兼容) ===")
    print(f"  speaker_count: {story.get('speaker_count')}")
    print(f"  speakers: {len(story.get('speakers', []))} 个")
    print(f"  background_audio_url: {story.get('background_audio_url')}")


async def list_stories():
    """列出最近的故事"""
    from core.database.mongodb import get_database

    db = get_database()
    collection = db["stories"]

    cursor = collection.find({}).sort("created_at", -1).limit(10)
    stories = []
    async for doc in cursor:
        stories.append(doc)

    total = await collection.count_documents({})

    print(f"\n=== 最近的故事 (共 {total} 个) ===")
    for s in stories:
        single_ok = "OK" if s.get('single_speaker_analysis', {}).get('is_analyzed') else "NO"
        dual_ok = "OK" if s.get('dual_speaker_analysis', {}).get('is_analyzed') else "NO"
        title = s.get('title') or s.get('title_en') or 'Untitled'
        title_short = title[:30] if len(title) > 30 else title
        print(f"  {str(s.get('_id'))}: {title_short:<30} Single:{single_ok} Dual:{dual_ok}")


async def main():
    # 先连接数据库
    from core.config.database import Database
    await Database.connect()

    try:
        if len(sys.argv) < 2:
            await list_stories()
            print("\n用法: python tests/check_story_analysis.py <story_id>")
        else:
            story_id = sys.argv[1]
            await check_story(story_id)
    finally:
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
