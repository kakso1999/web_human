"""
云端 Whisper 服务
使用 APIMart API 进行语音转文字
"""
import os
import logging
from typing import Optional

from .base import BaseWhisperService, WhisperResult
from core.utils.apimart_client import APIMartClient

logger = logging.getLogger(__name__)


class CloudWhisperService(BaseWhisperService):
    """APIMart 云端 Whisper 服务"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("APIMART_API_KEY")
        self._client: Optional[APIMartClient] = None

    async def _get_client(self) -> APIMartClient:
        """获取或创建 API 客户端"""
        if self._client is None:
            self._client = APIMartClient(api_key=self.api_key)
        return self._client

    async def transcribe(
        self,
        audio_path: str,
        language: str = "en"
    ) -> WhisperResult:
        """
        使用 APIMart Whisper-1 API 转录音频

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            WhisperResult: 转录结果
        """
        client = await self._get_client()

        logger.info(f"[Cloud Whisper] Transcribing: {audio_path}")

        result = await client.transcribe_audio(
            audio_path=audio_path,
            language=language,
            response_format="verbose_json"
        )

        logger.info(f"[Cloud Whisper] Done: {len(result.words)} words, {result.duration:.1f}s")

        return WhisperResult(
            text=result.text,
            language=result.language,
            duration=result.duration,
            words=result.words,
            segments=None
        )

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.close()
            self._client = None
