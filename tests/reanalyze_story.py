"""
重新分析故事并更新数据库

为已存在的故事重新执行分析，更新 single_speaker_analysis 和 dual_speaker_analysis 字段

用法：
python tests/reanalyze_story.py <story_id>
python tests/reanalyze_story.py --all  # 分析所有未完成的故事
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def reanalyze_story(story_id: str):
    """重新分析单个故事"""
    from core.config.database import Database
    from modules.story.repository import StoryRepository
    from modules.voice_separation import get_voice_separation_service
    from core.config.settings import get_settings
    from pathlib import Path

    settings = get_settings()
    repo = StoryRepository()

    # 获取故事信息
    story = await repo.get_by_id(story_id)

    if not story:
        print(f"[ERROR] 故事 {story_id} 不存在")
        return False

    video_url = story.get("video_url")
    print(f"\n=== 重新分析故事 ===")
    print(f"ID: {story_id}")
    print(f"标题: {story.get('title')}")
    print(f"视频URL: {video_url}")

    if not video_url:
        print("[ERROR] 故事没有视频URL")
        return False

    # 构建视频路径
    if video_url.startswith("/uploads/"):
        video_path = str(Path(settings.UPLOAD_DIR).parent / video_url.lstrip("/"))
    else:
        print(f"[ERROR] 不支持的视频URL格式: {video_url}")
        return False

    if not os.path.exists(video_path):
        print(f"[ERROR] 视频文件不存在: {video_path}")
        return False

    print(f"视频路径: {video_path}")

    # 调用 analyze_both_modes
    print("\n开始分析...")
    voice_service = get_voice_separation_service()

    try:
        result = await voice_service.analyze_both_modes(story_id, video_path)

        single_analysis = result.get("single_speaker_analysis")
        dual_analysis = result.get("dual_speaker_analysis")
        errors = result.get("errors")

        print(f"\n分析结果:")
        print(f"  单人模式: {'成功' if single_analysis else '失败'}")
        print(f"  双人模式: {'成功' if dual_analysis else '失败'}")

        if errors:
            print(f"  错误: {errors}")

        # 构建更新数据
        update_data = {
            "is_analyzed": True,
            "analysis_error": None
        }

        if single_analysis:
            update_data["single_speaker_analysis"] = single_analysis

        if dual_analysis:
            update_data["dual_speaker_analysis"] = dual_analysis
            # 保持旧字段兼容性
            update_data["speaker_count"] = len(dual_analysis.get("speakers", []))
            update_data["speakers"] = dual_analysis.get("speakers", [])
            update_data["background_audio_url"] = dual_analysis.get("background_url")
            update_data["diarization_segments"] = dual_analysis.get("diarization_segments", [])

        # 如果两种分析都失败，记录错误
        if errors and not single_analysis and not dual_analysis:
            update_data["is_analyzed"] = False
            update_data["analysis_error"] = "; ".join(errors)

        # 更新数据库
        print("\n更新数据库...")
        success = await repo.update(story_id, update_data)

        if success:
            print("[OK] 数据库更新成功")
        else:
            print("[WARN] 数据库更新失败 (可能没有变化)")

        return True

    except Exception as e:
        print(f"\n[ERROR] 分析失败: {e}")
        import traceback
        traceback.print_exc()

        # 记录错误到数据库
        await repo.update(story_id, {
            "is_analyzed": False,
            "analysis_error": str(e)
        })
        return False


async def reanalyze_all():
    """重新分析所有未完成新字段的故事"""
    from core.database.mongodb import get_database

    db = get_database()
    collection = db["stories"]

    # 查找 single_speaker_analysis 或 dual_speaker_analysis 为空的故事
    cursor = collection.find({
        "$or": [
            {"single_speaker_analysis": None},
            {"single_speaker_analysis": {"$exists": False}},
            {"dual_speaker_analysis": None},
            {"dual_speaker_analysis": {"$exists": False}}
        ]
    })

    stories = []
    async for doc in cursor:
        stories.append({
            "id": str(doc["_id"]),
            "title": doc.get("title") or doc.get("title_en") or "Untitled",
            "video_url": doc.get("video_url")
        })

    print(f"\n找到 {len(stories)} 个需要重新分析的故事")

    for i, story in enumerate(stories):
        print(f"\n[{i+1}/{len(stories)}] 处理: {story['title']}")

        if not story.get("video_url"):
            print("  跳过: 没有视频URL")
            continue

        await reanalyze_story(story["id"])
        print()


async def main():
    from core.config.database import Database
    await Database.connect()

    try:
        if len(sys.argv) < 2:
            print("用法:")
            print("  python tests/reanalyze_story.py <story_id>")
            print("  python tests/reanalyze_story.py --all")
            return

        if sys.argv[1] == "--all":
            await reanalyze_all()
        else:
            story_id = sys.argv[1]
            await reanalyze_story(story_id)

    finally:
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
