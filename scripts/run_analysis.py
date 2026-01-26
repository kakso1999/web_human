"""
手动触发故事AI分析 (英文输出)
"""
import asyncio
import os
import sys

# 设置环境变量
os.environ['APIMART_API_KEY'] = 'sk-JkVGFe5p6OYCcwR0X2Y5tdRgYdMAYKRGtxe6uqookaclh5Xn'

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.database import Database
from core.config.settings import get_settings
from modules.story.analysis_service import get_story_analysis_service

settings = get_settings()


async def run_analysis(force_reanalyze=False):
    await Database.connect()
    db = Database.get_db()

    # 获取故事
    if force_reanalyze:
        # 重新分析所有最新的5个故事
        stories = await db.stories.find({}).sort('created_at', -1).limit(5).to_list(5)
    else:
        # 只分析未分析的故事
        stories = await db.stories.find({
            'is_analyzed': False
        }).sort('created_at', -1).limit(10).to_list(10)

    print(f'找到 {len(stories)} 个待分析故事')

    if not stories:
        print('没有待分析的故事')
        await Database.disconnect()
        return

    analysis_service = get_story_analysis_service()

    for s in stories:
        story_id = str(s['_id'])
        video_url = s.get('video_url', '')

        if video_url.startswith('/uploads/'):
            video_path = os.path.join(settings.UPLOAD_DIR, video_url[9:])
        else:
            video_path = video_url

        print(f'\n处理: {story_id}')
        print(f'  视频: {video_path}')

        if not os.path.exists(video_path):
            print(f'  错误: 文件不存在')
            continue

        # 设为处理中
        await db.stories.update_one({'_id': s['_id']}, {'$set': {'is_processing': True}})

        try:
            result = await analysis_service.analyze_story(story_id, video_path, 'en')

            if result['success']:
                ai = result.get('ai_analysis', {})

                # 将 AI 分析的 segments 转换为 subtitles 格式
                subtitles = []
                for seg in ai.get('segments', []):
                    subtitles.append({
                        'start': seg.get('start', 0),
                        'end': seg.get('end', 0),
                        'text': seg.get('text', ''),
                        'voice': seg.get('voice', 'VOICE_1')
                    })

                # 构建双声部 speakers（VOICE_1 和 VOICE_2）
                dual_assignment = ai.get('dual_voice_assignment', {})
                original_speakers_map = {sp.get('speaker_id', sp.get('id', '')): sp for sp in ai.get('original_speakers', [])}

                dual_speakers = []
                for voice_id in ['VOICE_1', 'VOICE_2']:
                    assigned_chars = dual_assignment.get(voice_id, [])
                    if assigned_chars:
                        descriptions = []
                        for char_id in assigned_chars:
                            char_info = original_speakers_map.get(char_id, {})
                            desc = char_info.get('description', char_id)
                            descriptions.append(desc)

                        dual_speakers.append({
                            'speaker_id': voice_id,
                            'label': voice_id.replace('_', ' ').title(),
                            'description': ', '.join(descriptions),
                            'gender': 'unknown',
                            'duration': 0.0,
                            'assigned_characters': assigned_chars
                        })

                # 计算总时长
                total_duration = sum(seg.get('end', 0) - seg.get('start', 0) for seg in subtitles) if subtitles else 0

                await db.stories.update_one({'_id': s['_id']}, {'$set': {
                    'is_processing': False,
                    'is_analyzed': True,
                    'title': ai.get('title', ''),
                    'title_en': ai.get('title_en', ''),
                    'description': ai.get('description', ''),
                    'description_en': ai.get('description_en', ''),
                    'speaker_count': len(dual_speakers),
                    'speakers': dual_speakers,
                    'subtitles': subtitles,
                    'word_timestamps': result.get('word_timestamps', []),
                    'ai_analysis': ai,
                    # 单人模式分析结果 - 用于用户端选择
                    'single_speaker_analysis': {
                        'is_analyzed': True,
                        'vocals_url': None,
                        'background_url': None,
                        'duration': total_duration
                    },
                    # 双人模式分析结果 - 用于用户端选择
                    'dual_speaker_analysis': {
                        'is_analyzed': True,
                        'speakers': dual_speakers,
                        'background_url': None,
                        'diarization_segments': subtitles
                    }
                }})
                print(f'  成功! 标题: {ai.get("title_en") or ai.get("title")}')
            else:
                await db.stories.update_one({'_id': s['_id']}, {'$set': {'is_processing': False}})
                print(f'  失败: {result.get("error")}')
        except Exception as e:
            await db.stories.update_one({'_id': s['_id']}, {'$set': {'is_processing': False}})
            print(f'  异常: {e}')
            import traceback
            traceback.print_exc()

    await Database.disconnect()
    print('\n分析完成!')


if __name__ == '__main__':
    import sys
    force = '--force' in sys.argv or '-f' in sys.argv
    asyncio.run(run_analysis(force_reanalyze=force))
