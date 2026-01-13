"""
Voice Clone Service - 阿里云 CosyVoice 声音克隆服务
使用 DashScope SDK 实现声音克隆和语音合成
"""

import os
import asyncio
import time
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import uuid

# DNS 补丁：解决本地 DNS 服务器无法解析阿里云域名的问题
try:
    from core.utils.dns_patch import patch_dns
except ImportError:
    pass

from core.config.settings import get_settings

settings = get_settings()

# 配置代理绕过：阿里云域名不走代理
_no_proxy_domains = "aliyuncs.com,dashscope.aliyuncs.com,alibabacloud.com"
_existing_no_proxy = os.environ.get("NO_PROXY", os.environ.get("no_proxy", ""))
if _existing_no_proxy:
    if "aliyuncs.com" not in _existing_no_proxy:
        os.environ["NO_PROXY"] = f"{_existing_no_proxy},{_no_proxy_domains}"
else:
    os.environ["NO_PROXY"] = _no_proxy_domains
os.environ["no_proxy"] = os.environ["NO_PROXY"]

# 任务状态存储（内存中，生产环境可改用 Redis）
voice_clone_tasks: Dict[str, dict] = {}


class VoiceCloneService:
    """语音克隆服务 - 使用阿里云 CosyVoice API"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.backend_public_url = settings.BACKEND_PUBLIC_URL
        self.media_bed_url = settings.MEDIA_BED_URL
        self.upload_dir = Path(settings.UPLOAD_DIR) / "voice_clones"
        self.references_dir = self.upload_dir / "references"
        self.previews_dir = self.upload_dir / "previews"

        # 确保目录存在
        self.references_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 DashScope
        if self.api_key:
            import dashscope
            dashscope.api_key = self.api_key

    async def upload_to_media_bed(self, file_path: str) -> Optional[str]:
        """
        上传文件到图床服务

        Args:
            file_path: 本地文件路径

        Returns:
            公网可访问的 URL，失败返回 None
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return None

            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f, 'audio/wav')}
                    response = await client.post(
                        f"{self.media_bed_url}/upload",
                        files=files
                    )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        # 返回完整的公网 URL
                        file_url = result.get('url', '')
                        full_url = f"{self.media_bed_url}{file_url}"
                        print(f"Uploaded to media bed: {full_url}")
                        return full_url

                print(f"Media bed upload failed: {response.text}")
                return None

        except Exception as e:
            print(f"Media bed upload error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def check_service_health(self) -> bool:
        """检查 DashScope API 是否可用"""
        if not self.api_key:
            return False
        if not self.backend_public_url:
            return False
        return True

    async def generate_preview(
        self,
        task_id: str,
        reference_audio_path: str,
        text: str
    ):
        """
        使用阿里云 CosyVoice 生成语音克隆预览

        流程:
        1. 上传音频到图床服务获取公网 URL
        2. 创建音色 (create_voice) - 需要音频 URL
        3. 轮询查询音色状态 (query_voice) - 等待状态为 OK
        4. 使用音色进行语音合成 (SpeechSynthesizer.call)

        Args:
            task_id: 任务ID
            reference_audio_path: 参考音频路径
            text: 要生成的文本
        """
        try:
            # 更新任务状态
            voice_clone_tasks[task_id]["status"] = "processing"
            voice_clone_tasks[task_id]["progress"] = 5

            # 检查配置
            if not self.api_key:
                raise Exception("DASHSCOPE_API_KEY not configured in .env")

            voice_clone_tasks[task_id]["progress"] = 10

            # 上传音频到图床服务获取公网 URL
            print(f"[{task_id}] Uploading audio to media bed...")
            audio_url = await self.upload_to_media_bed(reference_audio_path)

            if not audio_url:
                raise Exception("Failed to upload audio to media bed service")

            print(f"[{task_id}] Audio URL: {audio_url}")

            voice_clone_tasks[task_id]["progress"] = 20

            # Step 1: 创建音色
            print(f"[{task_id}] Creating voice from reference audio...")
            voice_id = await self._create_voice(task_id, audio_url)

            if not voice_id:
                raise Exception("Failed to create voice - check if audio URL is accessible")

            voice_clone_tasks[task_id]["progress"] = 30

            # Step 2: 等待音色就绪
            print(f"[{task_id}] Waiting for voice to be ready: {voice_id}")
            voice_ready = await self._wait_for_voice_ready(task_id, voice_id)

            if not voice_ready:
                raise Exception("Voice enrollment failed or timed out")

            voice_clone_tasks[task_id]["progress"] = 60

            # Step 3: 使用音色合成语音
            print(f"[{task_id}] Synthesizing speech with cloned voice...")
            audio_data = await self._synthesize_speech(task_id, voice_id, text)

            if not audio_data:
                raise Exception("Speech synthesis failed")

            voice_clone_tasks[task_id]["progress"] = 90

            # Step 4: 保存音频文件
            output_filename = f"{task_id}.mp3"
            output_path = self.previews_dir / output_filename

            with open(output_path, 'wb') as f:
                f.write(audio_data)

            # 更新任务状态为完成
            voice_clone_tasks[task_id]["status"] = "completed"
            voice_clone_tasks[task_id]["progress"] = 100
            voice_clone_tasks[task_id]["audio_url"] = f"/uploads/voice_clones/previews/{output_filename}"
            voice_clone_tasks[task_id]["completed_at"] = datetime.utcnow()
            # 保存声音信息以便后续保存档案
            voice_clone_tasks[task_id]["voice_id"] = voice_id
            voice_clone_tasks[task_id]["reference_audio_url"] = audio_url
            voice_clone_tasks[task_id]["reference_audio_local"] = reference_audio_path

            print(f"[{task_id}] Voice clone completed successfully")

        except Exception as e:
            print(f"[{task_id}] Voice clone failed: {e}")
            import traceback
            traceback.print_exc()

            voice_clone_tasks[task_id]["status"] = "failed"
            voice_clone_tasks[task_id]["error"] = str(e)
            voice_clone_tasks[task_id]["progress"] = 0

    async def _create_voice(self, task_id: str, audio_url: str) -> Optional[str]:
        """
        创建音色（声音复刻）

        Args:
            task_id: 任务ID
            audio_url: 音频公网 URL

        Returns:
            voice_id 或 None
        """
        try:
            from dashscope.audio.tts_v2 import VoiceEnrollmentService

            service = VoiceEnrollmentService()

            # 生成唯一的音色前缀（仅数字和小写字母，<10字符）
            voice_prefix = f"ec{uuid.uuid4().hex[:6]}"

            # 使用 asyncio.to_thread 在线程池中运行同步的 SDK 调用
            # 避免阻塞 asyncio 事件循环
            def create_voice_sync():
                return service.create_voice(
                    target_model='cosyvoice-v2',
                    prefix=voice_prefix,
                    url=audio_url
                )

            voice_id = await asyncio.to_thread(create_voice_sync)

            if voice_id:
                print(f"[{task_id}] Voice created: {voice_id}")
                request_id = await asyncio.to_thread(service.get_last_request_id)
                print(f"[{task_id}] Request ID: {request_id}")
                return voice_id
            else:
                print(f"[{task_id}] Failed to create voice")
                return None

        except Exception as e:
            print(f"[{task_id}] Create voice error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _wait_for_voice_ready(
        self,
        task_id: str,
        voice_id: str,
        max_attempts: int = 30,
        poll_interval: int = 5
    ) -> bool:
        """
        轮询等待音色就绪

        Args:
            task_id: 任务ID
            voice_id: 音色ID
            max_attempts: 最大尝试次数
            poll_interval: 轮询间隔（秒）

        Returns:
            是否就绪
        """
        try:
            from dashscope.audio.tts_v2 import VoiceEnrollmentService

            service = VoiceEnrollmentService()

            for attempt in range(max_attempts):
                try:
                    # 使用 asyncio.to_thread 在线程池中运行同步调用
                    voice_info = await asyncio.to_thread(
                        service.query_voice, voice_id=voice_id
                    )
                    status = voice_info.get("status")
                    print(f"[{task_id}] Voice status (attempt {attempt + 1}/{max_attempts}): {status}")

                    if status == "OK":
                        return True
                    elif status in ["UNDEPLOYED", "FAILED"]:
                        print(f"[{task_id}] Voice enrollment failed: {status}")
                        return False

                    # 更新进度
                    progress = 30 + int((attempt / max_attempts) * 30)
                    voice_clone_tasks[task_id]["progress"] = min(progress, 55)

                except Exception as e:
                    print(f"[{task_id}] Query voice error: {e}")

                await asyncio.sleep(poll_interval)

            print(f"[{task_id}] Voice enrollment timed out")
            return False

        except Exception as e:
            print(f"[{task_id}] Wait for voice error: {e}")
            return False

    async def _synthesize_speech(
        self,
        task_id: str,
        voice_id: str,
        text: str
    ) -> Optional[bytes]:
        """
        使用克隆的音色合成语音

        Args:
            task_id: 任务ID
            voice_id: 音色ID
            text: 要合成的文本

        Returns:
            音频二进制数据
        """
        try:
            from dashscope.audio.tts_v2 import SpeechSynthesizer

            # 使用 asyncio.to_thread 在线程池中运行同步的 SDK 调用
            def synthesize_sync():
                synthesizer = SpeechSynthesizer(
                    model='cosyvoice-v2',
                    voice=voice_id
                )
                return synthesizer.call(text)

            audio_data = await asyncio.to_thread(synthesize_sync)

            if audio_data:
                print(f"[{task_id}] Speech synthesis completed, audio size: {len(audio_data)} bytes")
                return audio_data
            else:
                print(f"[{task_id}] Speech synthesis returned empty data")
                return None

        except Exception as e:
            print(f"[{task_id}] Synthesis error: {e}")
            import traceback
            traceback.print_exc()
            return None

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
        预加载检查 - 检查 DashScope API 配置
        """
        try:
            if self.api_key:
                print("DashScope API Key configured")
            else:
                print("Warning: DASHSCOPE_API_KEY not set in .env")

            if self.backend_public_url:
                print(f"Backend public URL: {self.backend_public_url}")
            else:
                print("Warning: BACKEND_PUBLIC_URL not set in .env (required for voice clone)")

        except Exception as e:
            print(f"Voice clone service check failed: {e}")

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

    async def save_voice_profile(self, user_id: str, task_id: str, name: str) -> Optional[dict]:
        """
        保存声音档案到数据库

        Args:
            user_id: 用户ID
            task_id: 任务ID
            name: 声音名称

        Returns:
            保存的档案信息
        """
        from .repository import voice_profile_repository

        # 获取任务信息
        task = voice_clone_tasks.get(task_id)
        if not task:
            return None

        if task.get("status") != "completed":
            return None

        # 检查是否属于该用户
        if not task_id.startswith(user_id):
            return None

        # 创建档案
        profile_data = {
            "user_id": user_id,
            "name": name,
            "voice_id": task.get("voice_id"),
            "reference_audio_url": task.get("reference_audio_url"),
            "reference_audio_local": task.get("reference_audio_local"),
            "preview_audio_url": task.get("audio_url"),
            "status": "active"
        }

        profile_id = await voice_profile_repository.create(profile_data)
        profile_data["id"] = profile_id

        return profile_data

    async def get_user_voice_profiles(self, user_id: str) -> list:
        """获取用户的所有声音档案"""
        from .repository import voice_profile_repository
        return await voice_profile_repository.get_by_user_id(user_id)

    async def get_voice_profile(self, profile_id: str, user_id: str) -> Optional[dict]:
        """获取单个声音档案"""
        from .repository import voice_profile_repository
        profile = await voice_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return profile
        return None

    async def update_voice_profile(self, profile_id: str, user_id: str, name: str) -> bool:
        """更新声音档案名称"""
        from .repository import voice_profile_repository
        profile = await voice_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return await voice_profile_repository.update(profile_id, {"name": name})
        return False

    async def delete_voice_profile(self, profile_id: str, user_id: str) -> bool:
        """删除声音档案"""
        from .repository import voice_profile_repository
        profile = await voice_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return await voice_profile_repository.delete(profile_id)
        return False


# 全局服务实例
voice_clone_service = VoiceCloneService()
