"""
Story AI 分析服务
使用 APIMart API 进行字幕提取和说话人分析
"""
import os
import logging
import subprocess
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from core.config.settings import get_settings, BASE_DIR
from core.utils.apimart_client import APIMartClient

logger = logging.getLogger(__name__)
settings = get_settings()


class StoryAnalysisService:
    """故事 AI 分析服务"""

    def __init__(self):
        self.upload_dir = Path(BASE_DIR) / settings.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_story(
        self,
        story_id: str,
        video_path: str,
        language: str = "en",
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        分析故事视频，提取字幕和说话人信息

        Args:
            story_id: 故事 ID
            video_path: 视频文件路径
            language: 语言代码 (en, zh)
            on_progress: 进度回调函数

        Returns:
            分析结果字典
        """
        result = {
            "success": False,
            "error": None,
            "word_timestamps": [],
            "ai_analysis": None,
            "duration": 0,
            "text": ""
        }

        try:
            # 步骤 1: 提取音频
            if on_progress:
                await on_progress("extracting_audio", 10)

            logger.info(f"[{story_id}] 步骤1: 提取音频")
            audio_path = await self._extract_audio(story_id, video_path)

            if not audio_path or not os.path.exists(audio_path):
                raise Exception("音频提取失败")

            # 步骤 2: 调用 Whisper-1 API 转录
            if on_progress:
                await on_progress("transcribing", 30)

            logger.info(f"[{story_id}] 步骤2: 调用 Whisper-1 API 转录")
            async with APIMartClient() as client:
                whisper_result = await client.transcribe_audio(
                    audio_path=audio_path,
                    language=language,
                    response_format="verbose_json"
                )

            result["word_timestamps"] = whisper_result.words
            result["duration"] = whisper_result.duration
            result["text"] = whisper_result.text

            logger.info(f"[{story_id}] 转录完成: {len(whisper_result.words)} 词, {whisper_result.duration:.1f}秒")

            # 步骤 3: 调用 Gemini API 分析说话人
            if on_progress:
                await on_progress("analyzing_speakers", 60)

            logger.info(f"[{story_id}] 步骤3: 调用 Gemini API 分析说话人")
            async with APIMartClient() as client:
                # 格式化字幕
                formatted_transcript = client.format_words_for_analysis(
                    whisper_result.words,
                    max_segments=100
                )

                # 分析说话人
                analysis_result = await client.analyze_speakers(
                    transcript_with_timestamps=formatted_transcript,
                    story_language=language
                )

            # 转换为字典格式
            # 确保 speakers 使用 speaker_id 字段
            speakers = []
            for sp in analysis_result.original_speakers:
                speaker = {
                    "speaker_id": sp.get("speaker_id") or sp.get("id", "UNKNOWN"),
                    "description": sp.get("description", ""),
                    "label": sp.get("label", ""),
                    "gender": sp.get("gender", "unknown"),
                    "audio_url": sp.get("audio_url"),
                    "duration": sp.get("duration", 0.0)
                }
                speakers.append(speaker)

            result["ai_analysis"] = {
                "title": analysis_result.title,
                "title_en": analysis_result.title_en,
                "description": analysis_result.description,
                "description_en": analysis_result.description_en,
                "original_speakers": speakers,
                "dual_voice_assignment": analysis_result.dual_voice_assignment,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "voice": seg.voice,
                        "text": seg.text
                    }
                    for seg in analysis_result.segments
                ]
            }

            logger.info(f"[{story_id}] 分析完成: {len(analysis_result.original_speakers)} 说话人, "
                       f"{len(analysis_result.segments)} 分段")

            if on_progress:
                await on_progress("completed", 100)

            result["success"] = True

            # 清理临时音频文件
            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

        except Exception as e:
            logger.error(f"[{story_id}] 分析失败: {str(e)}", exc_info=True)
            result["error"] = str(e)

            if on_progress:
                await on_progress("failed", 0)

        return result

    async def _extract_audio(self, story_id: str, video_path: str) -> Optional[str]:
        """
        从视频中提取音频

        Args:
            story_id: 故事 ID
            video_path: 视频文件路径

        Returns:
            音频文件路径
        """
        # 创建临时目录
        temp_dir = self.upload_dir / "temp" / story_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        audio_path = temp_dir / "audio.mp3"

        # FFmpeg 命令
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # 不处理视频
            "-acodec", "libmp3lame",
            "-ar", "16000",  # 16kHz 采样率
            "-ac", "1",  # 单声道
            "-ab", "128k",  # 128kbps
            "-y",  # 覆盖输出文件
            str(audio_path)
        ]

        try:
            logger.info(f"[{story_id}] 执行 FFmpeg: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"[{story_id}] FFmpeg 错误: {stderr.decode()}")
                return None

            if not audio_path.exists():
                logger.error(f"[{story_id}] 音频文件未生成")
                return None

            logger.info(f"[{story_id}] 音频提取成功: {audio_path}")
            return str(audio_path)

        except Exception as e:
            logger.error(f"[{story_id}] 音频提取异常: {str(e)}", exc_info=True)
            return None


# 单例
_analysis_service: Optional[StoryAnalysisService] = None


def get_story_analysis_service() -> StoryAnalysisService:
    """获取故事分析服务"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = StoryAnalysisService()
    return _analysis_service
