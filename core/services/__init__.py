"""
Core Services

- whisper: 语音转文字服务 (支持本地/云端切换)
"""
from core.services.whisper import get_whisper_service, transcribe_audio

__all__ = ["get_whisper_service", "transcribe_audio"]
