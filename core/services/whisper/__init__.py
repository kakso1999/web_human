"""
Whisper 语音转文字服务

支持本地和云端两种模式：
- local: 使用本地 GPU 运行 Whisper large-v3 模型
- cloud: 使用 APIMart Whisper-1 API

切换方式：
1. 设置环境变量: WHISPER_SERVICE_MODE=local 或 WHISPER_SERVICE_MODE=cloud
2. 代码中指定: get_whisper_service("local") 或 get_whisper_service("cloud")
"""
from .base import BaseWhisperService, WhisperResult
from .factory import get_whisper_service, transcribe_audio, WHISPER_SERVICE_MODE

__all__ = [
    "BaseWhisperService",
    "WhisperResult",
    "get_whisper_service",
    "transcribe_audio",
    "WHISPER_SERVICE_MODE"
]
