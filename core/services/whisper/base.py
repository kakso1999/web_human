"""
Whisper 服务基类
定义语音转文字服务的统一接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class WhisperResult:
    """Whisper 转录结果"""
    text: str
    language: str
    duration: float
    words: List[Dict[str, Any]]  # [{"word": "xxx", "start": 1.0, "end": 1.5}, ...]
    segments: List[Dict[str, Any]] = None  # 分段信息


class BaseWhisperService(ABC):
    """Whisper 服务基类"""

    @abstractmethod
    async def transcribe(
        self,
        audio_path: str,
        language: str = "en"
    ) -> WhisperResult:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (en, zh, etc.)

        Returns:
            WhisperResult: 转录结果
        """
        pass

    @abstractmethod
    async def close(self):
        """关闭服务，释放资源"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
