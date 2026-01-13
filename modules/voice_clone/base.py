"""
Voice Clone Service 抽象基类
定义声音克隆服务的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path


class BaseVoiceCloneService(ABC):
    """声音克隆服务抽象基类"""

    @abstractmethod
    async def check_service_health(self) -> bool:
        """检查服务是否可用"""
        pass

    @abstractmethod
    async def generate_preview(
        self,
        task_id: str,
        reference_audio_path: str,
        text: str
    ) -> None:
        """
        生成语音克隆预览

        Args:
            task_id: 任务ID
            reference_audio_path: 参考音频路径
            text: 要生成的文本
        """
        pass

    @abstractmethod
    def create_task(self, user_id: str) -> str:
        """
        创建新的语音克隆任务

        Args:
            user_id: 用户ID

        Returns:
            任务ID
        """
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        pass

    @abstractmethod
    def save_reference_audio(self, user_id: str, file_content: bytes, filename: str) -> str:
        """
        保存用户上传的参考音频

        Args:
            user_id: 用户ID
            file_content: 文件内容
            filename: 原始文件名

        Returns:
            保存后的文件路径
        """
        pass

    @abstractmethod
    async def save_voice_profile(self, user_id: str, task_id: str, name: str) -> Optional[dict]:
        """保存声音档案"""
        pass

    @abstractmethod
    async def get_user_voice_profiles(self, user_id: str) -> list:
        """获取用户的所有声音档案"""
        pass

    @abstractmethod
    async def get_voice_profile(self, profile_id: str, user_id: str) -> Optional[dict]:
        """获取单个声音档案"""
        pass

    @abstractmethod
    async def update_voice_profile(self, profile_id: str, user_id: str, name: str) -> bool:
        """更新声音档案名称"""
        pass

    @abstractmethod
    async def delete_voice_profile(self, profile_id: str, user_id: str) -> bool:
        """删除声音档案"""
        pass

    @abstractmethod
    async def preload_model(self) -> None:
        """预加载模型"""
        pass

    @abstractmethod
    async def synthesize_speech(
        self,
        voice_profile_id: str,
        text: str,
        output_path: str
    ) -> Optional[str]:
        """
        使用声音档案合成语音

        Args:
            voice_profile_id: 声音档案ID
            text: 要合成的文本
            output_path: 输出文件路径

        Returns:
            输出文件路径，失败返回 None
        """
        pass

    @abstractmethod
    async def clone_audio_with_text(
        self,
        reference_audio_path: str,
        text: str,
        output_path: str
    ) -> Optional[str]:
        """
        使用参考音频克隆语音（不保存档案）

        Args:
            reference_audio_path: 参考音频路径
            text: 要合成的文本
            output_path: 输出文件路径

        Returns:
            输出文件路径，失败返回 None
        """
        pass
