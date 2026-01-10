"""
语音分离模块

使用 Demucs 分离人声/背景音
使用 Pyannote 进行说话人识别
"""
from .service import VoiceSeparationService, get_voice_separation_service

__all__ = ["VoiceSeparationService", "get_voice_separation_service"]
