"""
Digital Human Service Factory
工厂模式：根据配置选择本地或云端服务
"""

from typing import Union
from core.config.settings import get_settings

settings = get_settings()

# 服务实例缓存
_digital_human_service = None


def get_digital_human_service() -> Union['BaseDigitalHumanService', 'DigitalHumanService', 'LocalDigitalHumanService']:
    """
    获取数字人服务实例

    根据 AI_SERVICE_MODE 环境变量选择：
    - "local": 使用本地 FFmpeg 合成（图片+音频 → 视频）
    - "cloud": 使用阿里云 EMO API（口型同步）

    Returns:
        数字人服务实例
    """
    global _digital_human_service

    if _digital_human_service is not None:
        return _digital_human_service

    service_mode = getattr(settings, 'AI_SERVICE_MODE', 'cloud').lower()

    if service_mode == "local":
        print("[DigitalHumanFactory] Using LOCAL service (FFmpeg)")
        from .local_service import LocalDigitalHumanService
        _digital_human_service = LocalDigitalHumanService()
    else:
        print("[DigitalHumanFactory] Using CLOUD service (Aliyun EMO)")
        from .service import DigitalHumanService
        _digital_human_service = DigitalHumanService()

    return _digital_human_service


def reset_service():
    """重置服务实例（用于测试或切换模式）"""
    global _digital_human_service
    _digital_human_service = None


def get_service_mode() -> str:
    """获取当前服务模式"""
    return getattr(settings, 'AI_SERVICE_MODE', 'cloud').lower()


def is_local_mode() -> bool:
    """是否为本地模式"""
    return get_service_mode() == "local"
