"""
Local Digital Human Service - 本地数字人服务
使用 FFmpeg 将图片和音频合成为视频（非口型同步）
"""

import os
import asyncio
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from .base import BaseDigitalHumanService
from core.config.settings import get_settings

settings = get_settings()

# 任务状态存储
local_digital_human_tasks: Dict[str, dict] = {}


class LocalDigitalHumanService(BaseDigitalHumanService):
    """本地数字人服务 - 使用 FFmpeg 合成图片+音频视频"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.upload_dir = Path(settings.UPLOAD_DIR) / "digital_human"
        self.images_dir = self.upload_dir / "images"
        self.previews_dir = self.upload_dir / "previews"

        # 确保目录存在
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)

    def _convert_local_path_to_url(self, local_path: str) -> str:
        """
        将本地文件路径转换为可访问的 URL 路径
        例如: E:/uploads/digital_human/images/xxx.jpg
        转换为: /uploads/digital_human/images/xxx.jpg
        """
        if not local_path:
            return ""

        # 标准化路径分隔符
        normalized_path = local_path.replace("\\", "/")

        # 尝试多种方式提取 URL 路径
        # 方式1: 查找 /uploads/ 开头的部分
        if "/uploads/" in normalized_path:
            idx = normalized_path.find("/uploads/")
            return normalized_path[idx:]

        # 方式2: 查找 digital_human 目录
        if "digital_human" in normalized_path:
            idx = normalized_path.find("digital_human")
            return "/uploads/" + normalized_path[idx:]

        # 方式3: 只保留文件名，构建默认路径
        filename = os.path.basename(normalized_path)
        if filename:
            return f"/uploads/digital_human/images/{filename}"

        return normalized_path

    def _run_ffmpeg(self, cmd: list, desc: str = "") -> bool:
        """执行 FFmpeg 命令"""
        print(f"[FFmpeg] {desc}")
        print(f"  CMD: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:500]}")
            return False

        print(f"  OK")
        return True

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except:
            return 0.0

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

        本地模式：将图片和音频合成为静态视频（图片不动）
        """
        from .schemas import AudioSourceType

        if audio_source is None:
            audio_source = AudioSourceType.DEFAULT

        try:
            local_digital_human_tasks[task_id]["status"] = "processing"
            local_digital_human_tasks[task_id]["progress"] = 10

            # Step 1: 获取音频
            print(f"[{task_id}] Preparing audio...")

            actual_audio_path = None

            if audio_source == AudioSourceType.UPLOAD and audio_path:
                # 使用上传的音频
                actual_audio_path = audio_path
            elif audio_source == AudioSourceType.VOICE_PROFILE and voice_profile_id:
                # 使用声音档案合成
                actual_audio_path = await self._synthesize_with_voice_profile(
                    task_id, voice_profile_id, preview_text
                )
            else:
                # 默认：使用本地 TTS 生成
                actual_audio_path = await self._generate_local_tts(task_id, preview_text)

            if not actual_audio_path:
                raise Exception("Failed to prepare audio")

            local_digital_human_tasks[task_id]["progress"] = 40

            # Step 2: 生成视频
            print(f"[{task_id}] Generating video...")
            local_digital_human_tasks[task_id]["status"] = "generating"

            output_filename = f"{task_id}.mp4"
            output_path = self.previews_dir / output_filename

            success = await asyncio.to_thread(
                self._generate_video, image_path, actual_audio_path, str(output_path)
            )

            if not success:
                raise Exception("Video generation failed")

            local_digital_human_tasks[task_id]["progress"] = 90

            # 完成
            local_digital_human_tasks[task_id]["status"] = "completed"
            local_digital_human_tasks[task_id]["progress"] = 100
            local_digital_human_tasks[task_id]["video_url"] = f"/uploads/digital_human/previews/{output_filename}"
            local_digital_human_tasks[task_id]["image_url"] = self._convert_local_path_to_url(image_path)
            local_digital_human_tasks[task_id]["image_local"] = image_path
            local_digital_human_tasks[task_id]["completed_at"] = datetime.utcnow()

            print(f"[{task_id}] Digital human video completed: {output_path}")

        except Exception as e:
            print(f"[{task_id}] Digital human generation failed: {e}")
            import traceback
            traceback.print_exc()

            local_digital_human_tasks[task_id]["status"] = "failed"
            local_digital_human_tasks[task_id]["error"] = str(e)
            local_digital_human_tasks[task_id]["progress"] = 0

    def _generate_video(self, image_path: str, audio_path: str, output_path: str) -> bool:
        """
        使用 FFmpeg 将图片和音频合成视频

        创建一个静态图片 + 音频的视频
        """
        # 获取音频时长
        duration = self._get_audio_duration(audio_path)
        if duration <= 0:
            print(f"[FFmpeg] Invalid audio duration: {duration}")
            return False

        # 使用 FFmpeg 合成视频
        # -loop 1: 循环图片
        # -t: 持续时长与音频相同
        # -c:v libx264: H.264 编码
        # -tune stillimage: 优化静态图片
        # -c:a aac: AAC 音频编码
        # -pix_fmt yuv420p: 兼容性像素格式
        # -shortest: 以最短流为准
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-t", str(duration),
            "-shortest",
            str(output_path)
        ]

        return self._run_ffmpeg(cmd, f"Creating video ({duration:.1f}s)")

    async def _synthesize_with_voice_profile(
        self,
        task_id: str,
        voice_profile_id: str,
        text: str
    ) -> Optional[str]:
        """使用声音档案合成音频"""
        try:
            from modules.voice_clone.factory import get_voice_clone_service

            voice_service = get_voice_clone_service()
            output_path = str(self.previews_dir / f"{task_id}_audio.wav")

            result = await voice_service.synthesize_speech(
                voice_profile_id, text, output_path
            )

            return result

        except Exception as e:
            print(f"[{task_id}] Voice profile synthesis error: {e}")
            return None

    async def _generate_local_tts(self, task_id: str, text: str) -> Optional[str]:
        """使用本地 TTS 生成默认音频"""
        try:
            # 使用 edge-tts 或简单的 TTS
            output_path = str(self.previews_dir / f"{task_id}_default_audio.mp3")

            # 尝试使用 edge-tts
            try:
                import edge_tts

                communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                await communicate.save(output_path)
                return output_path

            except ImportError:
                print(f"[{task_id}] edge-tts not available, trying pyttsx3...")

            # 回退到 pyttsx3
            try:
                import pyttsx3

                output_path_wav = str(self.previews_dir / f"{task_id}_default_audio.wav")

                def generate():
                    engine = pyttsx3.init()
                    engine.save_to_file(text, output_path_wav)
                    engine.runAndWait()

                await asyncio.to_thread(generate)
                return output_path_wav

            except ImportError:
                print(f"[{task_id}] pyttsx3 not available")

            # 如果都不可用，生成静音音频
            print(f"[{task_id}] No TTS available, generating silent audio...")
            return await self._generate_silent_audio(task_id, 3.0)  # 3秒静音

        except Exception as e:
            print(f"[{task_id}] Local TTS error: {e}")
            return None

    async def _generate_silent_audio(self, task_id: str, duration: float) -> str:
        """生成静音音频"""
        import numpy as np
        import soundfile as sf

        output_path = str(self.previews_dir / f"{task_id}_silent.wav")
        sample_rate = 16000
        samples = int(duration * sample_rate)
        silent_audio = np.zeros(samples)
        sf.write(output_path, silent_audio, sample_rate)
        return output_path

    def create_task(self, user_id: str) -> str:
        """创建新任务"""
        task_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

        local_digital_human_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "video_url": None,
            "image_url": None,
            "face_bbox": None,
            "ext_bbox": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None
        }

        return task_id

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        return local_digital_human_tasks.get(task_id)

    def save_image(self, user_id: str, file_content: bytes, filename: str) -> str:
        """保存头像图片"""
        ext = Path(filename).suffix or ".jpg"
        new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = self.images_dir / new_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    def save_audio(self, user_id: str, file_content: bytes, filename: str) -> str:
        """保存音频文件"""
        ext = Path(filename).suffix or ".wav"
        new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = self.previews_dir / new_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    async def save_avatar_profile(self, user_id: str, task_id: str, name: str) -> Optional[dict]:
        """保存头像档案"""
        from .repository import avatar_profile_repository

        task = local_digital_human_tasks.get(task_id)
        if not task or task.get("status") != "completed":
            return None

        if not task_id.startswith(user_id):
            return None

        # 转换本地路径为 URL 路径
        image_local = task.get("image_local", "")
        image_url = self._convert_local_path_to_url(image_local) if image_local else task.get("image_url", "")

        profile_data = {
            "user_id": user_id,
            "name": name,
            "image_url": image_url,
            "image_local": image_local,
            "face_bbox": [],  # 本地模式不做人脸检测
            "ext_bbox": [],
            "preview_video_url": task.get("video_url"),
            "status": "active",
            "service_mode": "local"
        }

        profile_id = await avatar_profile_repository.create(profile_data)
        profile_data["id"] = profile_id

        return profile_data

    async def get_user_avatar_profiles(self, user_id: str) -> list:
        """获取用户头像档案"""
        from .repository import avatar_profile_repository
        return await avatar_profile_repository.get_by_user_id(user_id)

    async def get_avatar_profile(self, profile_id: str, user_id: str) -> Optional[dict]:
        """获取单个头像档案"""
        from .repository import avatar_profile_repository
        profile = await avatar_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return profile
        return None

    async def update_avatar_profile(self, profile_id: str, user_id: str, name: str) -> bool:
        """更新头像档案"""
        from .repository import avatar_profile_repository
        profile = await avatar_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return await avatar_profile_repository.update(profile_id, {"name": name})
        return False

    async def delete_avatar_profile(self, profile_id: str, user_id: str) -> bool:
        """删除头像档案"""
        from .repository import avatar_profile_repository
        profile = await avatar_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return await avatar_profile_repository.delete(profile_id)
        return False

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

        本地模式：忽略 face_bbox 和 ext_bbox，直接合成静态视频
        """
        try:
            success = await asyncio.to_thread(
                self._generate_video, image_path, audio_path, output_path
            )

            if success:
                return output_path
            return None

        except Exception as e:
            print(f"[LocalDigitalHuman] Generate video error: {e}")
            return None

    # ==================== 兼容云端接口的方法 ====================
    # 这些方法是为了兼容 story_generation 模块调用云端 EMO API 的代码
    # 本地模式下，直接使用 FFmpeg 合成视频，无需异步轮询

    async def _create_emo_task(
        self,
        task_id: str,
        image_url: str,
        audio_url: str,
        face_bbox: List[int],
        ext_bbox: List[int]
    ) -> Optional[str]:
        """
        创建 EMO 视频生成任务 (本地兼容版)

        本地模式下，存储任务参数，返回任务ID
        实际视频生成在 _wait_for_emo_task 中执行
        """
        try:
            # 存储任务参数到内存中，供后续处理
            self._emo_pending_tasks = getattr(self, '_emo_pending_tasks', {})
            self._emo_pending_tasks[task_id] = {
                'image_url': image_url,
                'audio_url': audio_url,
                'face_bbox': face_bbox,
                'ext_bbox': ext_bbox
            }
            print(f"[LocalDigitalHuman] Created local EMO task: {task_id}")
            return task_id  # 返回相同的 task_id 作为 emo_task_id
        except Exception as e:
            print(f"[LocalDigitalHuman] Create EMO task error: {e}")
            return None

    async def _wait_for_emo_task(
        self,
        task_id: str,
        emo_task_id: str,
        max_attempts: int = 120,
        poll_interval: int = 5
    ) -> Optional[str]:
        """
        等待 EMO 任务完成 (本地兼容版)

        本地模式下，直接执行视频合成并返回结果
        """
        import os
        import httpx
        import tempfile
        from core.config.settings import get_settings
        settings = get_settings()

        try:
            # 获取任务参数
            self._emo_pending_tasks = getattr(self, '_emo_pending_tasks', {})
            task_params = self._emo_pending_tasks.get(task_id)

            if not task_params:
                print(f"[LocalDigitalHuman] Task not found: {task_id}")
                return None

            image_url = task_params['image_url']
            audio_url = task_params['audio_url']

            # 辅助函数：获取文件内容（支持本地路径和HTTP URL）
            async def get_file_content(url: str, file_type: str) -> bytes:
                media_bed_url = getattr(settings, 'MEDIA_BED_URL', '')
                local_path = None

                if url.startswith(('http://', 'https://')):
                    # HTTP URL - 检查是否是媒体床 URL
                    if media_bed_url and url.startswith(media_bed_url):
                        # 媒体床 URL：在本地模式下转换为本地路径
                        url_path = url[len(media_bed_url):]
                        if url_path.startswith('/uploads/'):
                            local_path = os.path.join(settings.UPLOAD_DIR, url_path[len('/uploads/'):])
                        elif url_path.startswith('/'):
                            local_path = os.path.join(settings.UPLOAD_DIR, url_path.lstrip('/'))
                        print(f"[LocalDigitalHuman] Converting media bed URL to local path: {local_path}")
                else:
                    # 相对路径
                    local_path = url
                    if local_path.startswith('/uploads/'):
                        local_path = os.path.join(settings.UPLOAD_DIR, local_path[len('/uploads/'):])
                    elif local_path.startswith('/'):
                        local_path = local_path.lstrip('/')
                    if not os.path.isabs(local_path):
                        local_path = os.path.join(os.getcwd(), local_path)

                if local_path and os.path.exists(local_path):
                    print(f"[LocalDigitalHuman] Using local {file_type}: {local_path}")
                    with open(local_path, 'rb') as f:
                        return f.read()
                elif local_path:
                    print(f"[LocalDigitalHuman] Local {file_type} not found: {local_path}")
                    return None
                else:
                    # 非媒体床的外部 HTTP URL：尝试下载
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        print(f"[LocalDigitalHuman] Downloading {file_type}: {url[:80]}...")
                        try:
                            response = await client.get(url)
                            if response.status_code == 200:
                                return response.content
                            else:
                                print(f"[LocalDigitalHuman] Failed to download {file_type}: {response.status_code}")
                                return None
                        except Exception as e:
                            print(f"[LocalDigitalHuman] Download {file_type} error: {e}")
                            return None

            # 获取图片内容
            image_content = await get_file_content(image_url, "image")
            if not image_content:
                return None

            # 获取音频内容
            audio_content = await get_file_content(audio_url, "audio")
            if not audio_content:
                return None

            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
                img_file.write(image_content)
                image_path = img_file.name

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                audio_file.write(audio_content)
                audio_path = audio_file.name

            # 生成输出路径
            output_dir = os.path.join(settings.UPLOAD_DIR, 'story_generation', task_id.split('_')[0] if '_' in task_id else 'temp')
            os.makedirs(output_dir, exist_ok=True)
            output_filename = f"emo_{emo_task_id}_{int(asyncio.get_event_loop().time())}.mp4"
            output_path = os.path.join(output_dir, output_filename)

            # 生成视频
            print(f"[LocalDigitalHuman] Generating video for task: {task_id}")
            success = await asyncio.to_thread(
                self._generate_video, image_path, audio_path, output_path
            )

            # 清理临时文件
            try:
                os.unlink(image_path)
                os.unlink(audio_path)
            except:
                pass

            # 清理任务记录
            if task_id in self._emo_pending_tasks:
                del self._emo_pending_tasks[task_id]

            if success:
                # 返回相对 URL 路径
                relative_path = output_path.replace('\\', '/')
                if not relative_path.startswith('/'):
                    relative_path = '/' + relative_path
                print(f"[LocalDigitalHuman] Video generated: {relative_path}")
                return relative_path
            else:
                return None

        except Exception as e:
            print(f"[LocalDigitalHuman] Wait for EMO task error: {e}")
            import traceback
            traceback.print_exc()
            return None
