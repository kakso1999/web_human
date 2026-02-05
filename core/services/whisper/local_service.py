"""
本地 Whisper 服务
使用 OpenAI Whisper 模型进行本地语音转文字
仅用于本地开发测试，不要部署到服务器
"""
import os
import logging
import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from .base import BaseWhisperService, WhisperResult

logger = logging.getLogger(__name__)

# 本地模型配置
LOCAL_MODEL_PATH = "E:/local_models/whisper"
DEFAULT_MODEL = "large-v3"

# 线程池用于运行同步的 whisper 代码
_executor = ThreadPoolExecutor(max_workers=1)


class LocalWhisperService(BaseWhisperService):
    """本地 Whisper 服务 (GPU 加速)"""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str = "cuda"):
        """
        初始化本地 Whisper 服务

        Args:
            model_name: 模型名称 (tiny, base, small, medium, large-v3, turbo)
            device: 运行设备 (cuda, cpu)
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._loaded = False

    def _load_model(self):
        """加载 Whisper 模型 (同步)"""
        if self._loaded:
            return

        import whisper

        logger.info(f"[Local Whisper] Loading model '{self.model_name}' on {self.device}...")

        self._model = whisper.load_model(
            self.model_name,
            download_root=LOCAL_MODEL_PATH,
            device=self.device
        )
        self._loaded = True

        logger.info(f"[Local Whisper] Model loaded successfully")

    def _transcribe_sync(self, audio_path: str, language: str) -> dict:
        """同步转录 (在线程池中运行)"""
        self._load_model()

        logger.info(f"[Local Whisper] Transcribing: {audio_path}")

        result = self._model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            verbose=False
        )

        return result

    async def transcribe(
        self,
        audio_path: str,
        language: str = "en"
    ) -> WhisperResult:
        """
        使用本地 Whisper 模型转录音频

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            WhisperResult: 转录结果
        """
        loop = asyncio.get_event_loop()

        # 在线程池中运行同步的 whisper 代码
        result = await loop.run_in_executor(
            _executor,
            self._transcribe_sync,
            audio_path,
            language
        )

        # 提取词级时间戳
        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info.get("word", "").strip(),
                    "start": word_info.get("start", 0),
                    "end": word_info.get("end", 0)
                })

        # 计算总时长
        duration = 0
        if result.get("segments"):
            last_segment = result["segments"][-1]
            duration = last_segment.get("end", 0)

        logger.info(f"[Local Whisper] Done: {len(words)} words, {duration:.1f}s")

        return WhisperResult(
            text=result.get("text", "").strip(),
            language=result.get("language", language),
            duration=duration,
            words=words,
            segments=result.get("segments", [])
        )

    async def close(self):
        """释放模型资源"""
        if self._model is not None:
            # 清理 GPU 内存
            import torch
            del self._model
            self._model = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("[Local Whisper] Model unloaded")
