"""
Voice Clone Service - 调用独立语音克隆服务
通过 HTTP 调用 voice_clone_server (端口 8003) 进行语音克隆
"""

import os
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import uuid

from core.config.settings import get_settings

settings = get_settings()

# 从环境变量获取语音克隆服务地址
VOICE_CLONE_SERVICE_URL = settings.VOICE_CLONE_SERVICE_URL

# 任务状态存储（内存中，生产环境可改用 Redis）
voice_clone_tasks: Dict[str, dict] = {}


class VoiceCloneService:
    """语音克隆服务 - 调用独立服务"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.service_url = VOICE_CLONE_SERVICE_URL
        self.upload_dir = Path(settings.UPLOAD_DIR) / "voice_clones"
        self.references_dir = self.upload_dir / "references"
        self.previews_dir = self.upload_dir / "previews"

        # 确保目录存在
        self.references_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)

    async def check_service_health(self) -> bool:
        """检查独立服务是否可用"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.service_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("model_loaded", False)
            return False
        except:
            return False

    async def generate_preview(
        self,
        task_id: str,
        reference_audio_path: str,
        text: str
    ):
        """
        调用独立服务生成预览音频

        Args:
            task_id: 任务ID
            reference_audio_path: 参考音频路径
            text: 要生成的文本
        """
        try:
            # 更新任务状态
            voice_clone_tasks[task_id]["status"] = "processing"
            voice_clone_tasks[task_id]["progress"] = 10

            # 检查服务是否可用
            service_available = await self.check_service_health()
            if not service_available:
                raise Exception("语音克隆服务不可用，请确保 voice_clone_server 已启动 (端口 8003)")

            voice_clone_tasks[task_id]["progress"] = 20

            # 调用独立服务
            async with aiohttp.ClientSession() as session:
                # 准备文件上传
                with open(reference_audio_path, 'rb') as f:
                    audio_data = f.read()

                data = aiohttp.FormData()
                data.add_field('audio', audio_data,
                             filename=Path(reference_audio_path).name,
                             content_type='audio/wav')
                data.add_field('text', text)
                data.add_field('exaggeration', '0.5')
                data.add_field('cfg_weight', '0.5')

                voice_clone_tasks[task_id]["progress"] = 30

                # 发送请求到独立服务
                async with session.post(
                    f"{self.service_url}/clone",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10分钟超时
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"语音克隆服务返回错误: {error_text}")

                    result = await resp.json()

                    if not result.get("success"):
                        raise Exception(result.get("message", "语音生成失败"))

                    # 下载生成的音频
                    audio_url = result.get("audio_url")
                    if audio_url:
                        voice_clone_tasks[task_id]["progress"] = 80

                        # 从独立服务下载音频
                        async with session.get(f"{self.service_url}{audio_url}") as audio_resp:
                            if audio_resp.status == 200:
                                audio_content = await audio_resp.read()

                                # 保存到本地
                                output_filename = f"{task_id}.wav"
                                output_path = self.previews_dir / output_filename

                                with open(output_path, 'wb') as f:
                                    f.write(audio_content)

                                # 更新任务状态为完成
                                voice_clone_tasks[task_id]["status"] = "completed"
                                voice_clone_tasks[task_id]["progress"] = 100
                                voice_clone_tasks[task_id]["audio_url"] = f"/uploads/voice_clones/previews/{output_filename}"
                                voice_clone_tasks[task_id]["completed_at"] = datetime.utcnow()

                                print(f"任务 {task_id} 完成")
                                return

                    raise Exception("未能获取生成的音频")

        except Exception as e:
            print(f"任务 {task_id} 失败: {e}")
            import traceback
            traceback.print_exc()

            voice_clone_tasks[task_id]["status"] = "failed"
            voice_clone_tasks[task_id]["error"] = str(e)
            voice_clone_tasks[task_id]["progress"] = 0

    def create_task(self, user_id: str) -> str:
        """
        创建新的语音克隆任务

        Args:
            user_id: 用户ID

        Returns:
            任务ID
        """
        task_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

        voice_clone_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "audio_url": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None
        }

        return task_id

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典，不存在返回 None
        """
        return voice_clone_tasks.get(task_id)

    async def preload_model(self):
        """
        预加载检查 - 只检查独立服务是否可用
        """
        try:
            available = await self.check_service_health()
            if available:
                print("语音克隆服务已就绪 (端口 8003)")
            else:
                print("警告: 语音克隆服务未就绪，请启动 voice_clone_server")
        except Exception as e:
            print(f"检查语音克隆服务失败: {e}")

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
        # 生成唯一文件名
        ext = Path(filename).suffix or ".wav"
        new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = self.references_dir / new_filename

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)


# 全局服务实例
voice_clone_service = VoiceCloneService()
