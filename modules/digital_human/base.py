"""
Digital Human Service 抽象基类
定义数字人服务的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Any


class BaseDigitalHumanService(ABC):
    """数字人服务抽象基类"""

    @abstractmethod
    async def generate_preview(
        self,
        task_id: str,
        image_path: str,
        audio_source: Any = None,
        audio_path: str = None,
        voice_profile_id: str = None,
        preview_text: str = "Hello, I am your digital avatar. Nice to meet you!"
    ) -> None:
        """
        生成数字人预览视频

        Args:
            task_id: 任务ID
            image_path: 头像图片路径
            audio_source: 音频来源类型
            audio_path: 上传的音频文件路径
            voice_profile_id: 声音档案ID
            preview_text: 预览文本
        """
        pass

    @abstractmethod
    def create_task(self, user_id: str) -> str:
        """
        创建新的数字人任务

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
    def save_image(self, user_id: str, file_content: bytes, filename: str) -> str:
        """
        保存用户上传的头像图片

        Args:
            user_id: 用户ID
            file_content: 文件内容
            filename: 原始文件名

        Returns:
            保存后的文件路径
        """
        pass

    @abstractmethod
    def save_audio(self, user_id: str, file_content: bytes, filename: str) -> str:
        """
        保存用户上传的音频文件

        Args:
            user_id: 用户ID
            file_content: 文件内容
            filename: 原始文件名

        Returns:
            保存后的文件路径
        """
        pass

    @abstractmethod
    async def save_avatar_profile(self, user_id: str, task_id: str, name: str) -> Optional[dict]:
        """保存头像档案"""
        pass

    @abstractmethod
    async def get_user_avatar_profiles(self, user_id: str) -> list:
        """获取用户的所有头像档案"""
        pass

    @abstractmethod
    async def get_avatar_profile(self, profile_id: str, user_id: str) -> Optional[dict]:
        """获取单个头像档案"""
        pass

    @abstractmethod
    async def update_avatar_profile(self, profile_id: str, user_id: str, name: str) -> bool:
        """更新头像档案名称"""
        pass

    @abstractmethod
    async def delete_avatar_profile(self, profile_id: str, user_id: str) -> bool:
        """删除头像档案"""
        pass

    @abstractmethod
    async def generate_digital_human_video(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        face_bbox: List[int] = None,
        ext_bbox: List[int] = None
    ) -> Optional[str]:
        """
        生成数字人视频

        Args:
            image_path: 头像图片路径
            audio_path: 音频路径
            output_path: 输出视频路径
            face_bbox: 人脸检测框 (可选)
            ext_bbox: 扩展框 (可选)

        Returns:
            输出视频路径，失败返回 None
        """
        pass
