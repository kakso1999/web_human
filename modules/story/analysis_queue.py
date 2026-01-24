"""
故事分析队列服务
串行处理故事AI分析任务，避免API限流
"""
import asyncio
import os
import logging
from typing import Optional
from datetime import datetime

from core.config.database import Database
from core.config.settings import get_settings
from modules.story.analysis_service import get_story_analysis_service

logger = logging.getLogger(__name__)
settings = get_settings()


class StoryAnalysisQueue:
    """故事分析队列 - 单例模式"""

    _instance: Optional['StoryAnalysisQueue'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._current_story_id: Optional[str] = None

    async def start_worker(self):
        """启动队列工作者"""
        if self._is_running:
            logger.info("Story analysis worker already running")
            return

        self._is_running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Story analysis queue worker started")

    async def stop_worker(self):
        """停止队列工作者"""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Story analysis queue worker stopped")

    async def add_task(self, story_id: str, video_path: str, api_key: Optional[str] = None):
        """添加分析任务到队列"""
        task = {
            'story_id': story_id,
            'video_path': video_path,
            'api_key': api_key,
            'added_at': datetime.utcnow()
        }
        await self._queue.put(task)

        # 更新数据库状态
        db = Database.get_db()
        await db.stories.update_one(
            {'_id': self._to_object_id(story_id)},
            {'$set': {'is_processing': True, 'analysis_queued': True}}
        )

        queue_size = self._queue.qsize()
        logger.info(f"Story {story_id} added to analysis queue. Queue size: {queue_size}")
        return queue_size

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()

    def get_current_task(self) -> Optional[str]:
        """获取当前正在处理的故事ID"""
        return self._current_story_id

    async def _worker_loop(self):
        """工作者循环"""
        logger.info("Story analysis worker loop started")

        while self._is_running:
            try:
                # 等待任务，超时1秒以便检查是否应该停止
                try:
                    task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                story_id = task['story_id']
                video_path = task['video_path']
                api_key = task.get('api_key')
                retry_count = task.get('retry_count', 0)
                max_retries = 3

                self._current_story_id = story_id
                logger.info(f"Processing story analysis: {story_id} (retry: {retry_count})")

                try:
                    await self._process_story(story_id, video_path, api_key)
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error processing story {story_id}: {error_msg}")

                    # 检查是否是 API 限流错误
                    is_rate_limit = '超限额' in error_msg or 'rate limit' in error_msg.lower() or 'get_channel_failed' in error_msg

                    if is_rate_limit and retry_count < max_retries:
                        # 重新加入队列，等待更长时间
                        wait_time = 30 * (retry_count + 1)  # 30s, 60s, 90s
                        logger.info(f"API rate limited. Will retry {story_id} after {wait_time}s (retry {retry_count + 1}/{max_retries})")

                        # 更新状态
                        db = Database.get_db()
                        await db.stories.update_one(
                            {'_id': self._to_object_id(story_id)},
                            {'$set': {'analysis_retry_count': retry_count + 1, 'analysis_retry_at': datetime.utcnow()}}
                        )

                        # 等待后重新加入队列
                        await asyncio.sleep(wait_time)
                        task['retry_count'] = retry_count + 1
                        await self._queue.put(task)
                    else:
                        await self._mark_story_failed(story_id, error_msg)
                finally:
                    self._current_story_id = None
                    self._queue.task_done()

                # 处理完一个任务后等待，避免API限流
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                logger.info("Worker loop cancelled")
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(5)

    async def _process_story(self, story_id: str, video_path: str, api_key: Optional[str]):
        """处理单个故事分析"""
        db = Database.get_db()

        # 检查视频文件
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 设置环境变量（如果提供了API key）
        if api_key:
            os.environ['APIMART_API_KEY'] = api_key
        elif not os.getenv('APIMART_API_KEY'):
            # 从设置中获取
            apimart_key = getattr(settings, 'APIMART_API_KEY', None)
            if apimart_key:
                os.environ['APIMART_API_KEY'] = apimart_key

        # 执行分析
        analysis_service = get_story_analysis_service()
        result = await analysis_service.analyze_story(
            story_id=story_id,
            video_path=video_path,
            language='en'
        )

        if result['success']:
            ai = result.get('ai_analysis', {})

            # 将 AI 分析的 segments 转换为 subtitles 格式
            # segments 包含 VOICE_1/VOICE_2 分配的字幕分段
            subtitles = []
            for seg in ai.get('segments', []):
                subtitles.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', ''),
                    'voice': seg.get('voice', 'VOICE_1')
                })

            # 构建双声部 speakers（VOICE_1 和 VOICE_2）
            # 而不是显示所有原始角色
            dual_assignment = ai.get('dual_voice_assignment', {})
            original_speakers = {sp.get('speaker_id', sp.get('id', '')): sp for sp in ai.get('original_speakers', [])}

            dual_speakers = []
            for voice_id in ['VOICE_1', 'VOICE_2']:
                assigned_chars = dual_assignment.get(voice_id, [])
                if assigned_chars:
                    # 组合所有分配给该配音角色的原始角色描述
                    descriptions = []
                    for char_id in assigned_chars:
                        char_info = original_speakers.get(char_id, {})
                        desc = char_info.get('description', char_id)
                        descriptions.append(desc)

                    dual_speakers.append({
                        'speaker_id': voice_id,
                        'label': voice_id.replace('_', ' ').title(),  # "Voice 1" / "Voice 2"
                        'description': ', '.join(descriptions),  # "Narrator, Father"
                        'gender': 'unknown',
                        'duration': 0.0,
                        'assigned_characters': assigned_chars  # ["NARRATOR", "FATHER"]
                    })

            # 计算总时长
            total_duration = sum(seg.get('end', 0) - seg.get('start', 0) for seg in subtitles) if subtitles else 0

            update_data = {
                'is_processing': False,
                'is_analyzed': True,
                'analysis_queued': False,
                'title': ai.get('title', ''),
                'title_en': ai.get('title_en', ''),
                'description': ai.get('description', ''),
                'description_en': ai.get('description_en', ''),
                'speaker_count': len(dual_speakers),  # 2 (VOICE_1 + VOICE_2)
                'speakers': dual_speakers,  # 双声部配置
                'subtitles': subtitles,  # AI 分段字幕
                'word_timestamps': result.get('word_timestamps', []),
                'ai_analysis': ai,  # 保留完整 AI 分析结果
                'analyzed_at': datetime.utcnow(),
                # 单人模式分析结果 - 用于用户端选择
                'single_speaker_analysis': {
                    'is_analyzed': True,
                    'vocals_url': None,  # APIMart 分析不分离音轨
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
            }
            await db.stories.update_one(
                {'_id': self._to_object_id(story_id)},
                {'$set': update_data}
            )
            logger.info(f"Story {story_id} analysis completed. Title: {ai.get('title')}")
        else:
            error_msg = result.get('error', 'Unknown error')
            await self._mark_story_failed(story_id, error_msg)
            raise Exception(error_msg)

    async def _mark_story_failed(self, story_id: str, error: str):
        """标记故事分析失败"""
        db = Database.get_db()
        await db.stories.update_one(
            {'_id': self._to_object_id(story_id)},
            {'$set': {
                'is_processing': False,
                'analysis_queued': False,
                'analysis_error': error,
                'analysis_failed_at': datetime.utcnow()
            }}
        )
        logger.error(f"Story {story_id} analysis failed: {error}")

    def _to_object_id(self, id_str: str):
        """转换为 ObjectId"""
        from bson import ObjectId
        return ObjectId(id_str)


# 全局队列实例
_analysis_queue: Optional[StoryAnalysisQueue] = None


def get_analysis_queue() -> StoryAnalysisQueue:
    """获取分析队列实例"""
    global _analysis_queue
    if _analysis_queue is None:
        _analysis_queue = StoryAnalysisQueue()
    return _analysis_queue


async def start_analysis_worker():
    """启动分析队列工作者"""
    queue = get_analysis_queue()
    await queue.start_worker()


async def add_story_to_analysis_queue(story_id: str, video_path: str, api_key: Optional[str] = None) -> int:
    """添加故事到分析队列"""
    queue = get_analysis_queue()
    return await queue.add_task(story_id, video_path, api_key)
