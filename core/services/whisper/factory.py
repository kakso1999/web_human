"""
Whisper 服务工厂
根据配置切换本地/云端 Whisper 服务
"""
import logging
from typing import Optional

from .base import BaseWhisperService
from core.config.settings import get_settings

logger = logging.getLogger(__name__)

# Whisper 服务模式
# "local" - 使用本地 GPU 模型 (仅开发测试)
# "cloud" - 使用 APIMart API (生产环境)
WHISPER_SERVICE_MODE = get_settings().WHISPER_SERVICE_MODE


def get_whisper_service(mode: Optional[str] = None) -> BaseWhisperService:
    """
    获取 Whisper 服务实例

    Args:
        mode: 服务模式 ("local" 或 "cloud")，默认从环境变量读取

    Returns:
        BaseWhisperService: Whisper 服务实例

    Usage:
        # 使用默认模式（从环境变量 WHISPER_SERVICE_MODE 读取）
        service = get_whisper_service()

        # 强制使用本地模式
        service = get_whisper_service("local")

        # 强制使用云端模式
        service = get_whisper_service("cloud")

        # 使用服务
        async with get_whisper_service() as service:
            result = await service.transcribe("audio.mp3", language="en")
    """
    effective_mode = mode or WHISPER_SERVICE_MODE

    if effective_mode == "local":
        from .local_service import LocalWhisperService
        logger.info("[Whisper Factory] Creating LocalWhisperService (GPU)")
        return LocalWhisperService(model_name="large-v3", device="cuda")

    elif effective_mode == "cloud":
        from .cloud_service import CloudWhisperService
        logger.info("[Whisper Factory] Creating CloudWhisperService (APIMart)")
        return CloudWhisperService()

    else:
        raise ValueError(f"Unknown Whisper service mode: {effective_mode}")


# 便捷函数
async def transcribe_audio(
    audio_path: str,
    language: str = "en",
    mode: Optional[str] = None
) -> dict:
    """
    转录音频文件 (便捷函数)

    Args:
        audio_path: 音频文件路径
        language: 语言代码
        mode: 服务模式

    Returns:
        dict: 包含 text, words, duration 等字段
    """
    async with get_whisper_service(mode) as service:
        result = await service.transcribe(audio_path, language)
        return {
            "text": result.text,
            "language": result.language,
            "duration": result.duration,
            "words": result.words,
            "segments": result.segments
        }
