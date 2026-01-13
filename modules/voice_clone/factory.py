"""
Voice Clone Service Factory
工厂模式：根据配置选择本地或云端服务
"""

from typing import Union
from core.config.settings import get_settings

settings = get_settings()

# 服务实例缓存
_voice_clone_service = None


def get_voice_clone_service() -> Union['BaseVoiceCloneService', 'VoiceCloneService', 'LocalVoiceCloneService']:
    """
    获取声音克隆服务实例

    根据 AI_SERVICE_MODE 环境变量选择：
    - "local": 使用本地 SpeechT5 模型
    - "cloud": 使用阿里云 CosyVoice API

    Returns:
        声音克隆服务实例
    """
    global _voice_clone_service

    if _voice_clone_service is not None:
        return _voice_clone_service

    service_mode = getattr(settings, 'AI_SERVICE_MODE', 'cloud').lower()

    if service_mode == "local":
        print("[VoiceCloneFactory] Using LOCAL service (SpeechT5)")
        from .local_service import LocalVoiceCloneService
        _voice_clone_service = LocalVoiceCloneService()
    else:
        print("[VoiceCloneFactory] Using CLOUD service (Aliyun CosyVoice)")
        from .service import VoiceCloneService
        _voice_clone_service = VoiceCloneService()

    return _voice_clone_service


def reset_service():
    """重置服务实例（用于测试或切换模式）"""
    global _voice_clone_service
    _voice_clone_service = None


def get_service_mode() -> str:
    """获取当前服务模式"""
    return getattr(settings, 'AI_SERVICE_MODE', 'cloud').lower()


def is_local_mode() -> bool:
    """是否为本地模式"""
    return get_service_mode() == "local"
